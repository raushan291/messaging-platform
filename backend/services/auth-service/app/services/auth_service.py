from sqlalchemy.orm import Session
from app.repositories.user_repo import get_user_by_email
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, create_refresh_token
from fastapi import HTTPException, status
from app.models.user import User
from app.models.refresh_token import RefreshToken
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.repositories.refresh_token_repo import save_refresh_token, get_refresh_token, revoke_refresh_token

def login_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    save_refresh_token(db, db_token)

    return access_token, refresh_token

def register_user(db: Session, email: str, username: str, password: str):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user = User(
        email=email,
        username=username,
        password_hash=password_hash,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def refresh_tokens(db: Session, refresh_token_str: str):
    stored = get_refresh_token(db, refresh_token_str)
    if not stored:
        return None

    revoke_refresh_token(db, stored)

    payload = jwt.decode(
        refresh_token_str,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )

    user_id = payload["sub"]

    new_access = create_access_token({"sub": user_id})
    new_refresh = create_refresh_token({"sub": user_id})

    db_token = RefreshToken(
        user_id=user_id,
        token=new_refresh,
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    save_refresh_token(db, db_token)

    return new_access, new_refresh