from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserLoginRequest, UserRegisterRequest
from app.services.security_service import hash_password, verify_password
from app.utils.ids import new_uuid7


def register_user(payload: UserRegisterRequest, db: Session) -> User:
    """Create a user account if the email address is not already registered."""
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(
        id=new_uuid7(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(payload: UserLoginRequest, db: Session) -> User:
    """Return an active user when the supplied credentials are valid."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, str(user.password_hash)):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not bool(user.is_active):
        raise HTTPException(status_code=403, detail="User account is disabled")
    return user
