from typing import cast

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AuthResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.auth_service import authenticate_user, register_user
from app.services.security_service import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_response(user: User) -> UserResponse:
    """Convert a user database model into a public API response."""
    return UserResponse(
        id=cast(str, user.id),
        email=cast(str, user.email),
        created_at=user.created_at,
    )


def _set_auth_cookie(response: Response, user: User) -> None:
    """Attach a signed HttpOnly authentication cookie to the response."""
    token = create_access_token(cast(str, user.id))
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


@router.post("/register", response_model=AuthResponse)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a user and return its public profile."""
    user = register_user(payload, db)
    return AuthResponse(user=_to_user_response(user))


@router.post("/login", response_model=AuthResponse)
def login(
    payload: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate a user and set the HttpOnly JWT cookie."""
    user = authenticate_user(payload, db)
    _set_auth_cookie(response, user)
    return AuthResponse(user=_to_user_response(user))


@router.post("/logout")
def logout(response: Response):
    """Clear the authentication cookie for the current browser."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
    return {"message": "Logged out"}


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's public profile."""
    return AuthResponse(user=_to_user_response(current_user))
