from typing import cast

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.services.security_service import decode_access_token


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the HttpOnly JWT cookie."""
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_id = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not bool(user.is_active):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return cast(User, user)
