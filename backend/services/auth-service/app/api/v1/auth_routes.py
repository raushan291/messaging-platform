from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest
from app.schemas.user import UserResponse
from app.services.auth_service import login_user, register_user, refresh_tokens
from app.repositories.refresh_token_repo import get_refresh_token, revoke_refresh_token
from app.repositories.user_repo import get_user_by_email, get_user_by_id


router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    tokens = login_user(db, payload.email, payload.password)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": tokens[0],
        "refresh_token": tokens[1]
    }

@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(
        db=db,
        email=payload.email,
        username=payload.username,
        password=payload.password,
    )
    return user

@router.post("/logout")
def logout(refresh_token: str, db: Session = Depends(get_db)):
    token = get_refresh_token(db, refresh_token)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    revoke_refresh_token(db, token)
    return {"message": "Logged out"}

@router.post("/refresh")
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    tokens = refresh_tokens(db, refresh_token)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return {
        "access_token": tokens[0],
        "refresh_token": tokens[1],
    }

@router.post("/users/by_email/")
def get_users_by_email(emails: list[str] = Query(...), db: Session = Depends(get_db)):
    users_detail = []
    for email in emails:
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        users_detail.append({"id": user.id, "email": user.email, "username": user.username})

    return users_detail

@router.post("/users/by_id/")
def get_users_by_id(ids: list[str] = Query(...), db: Session = Depends(get_db)):
    users_detail = []
    for id in ids:
        user = get_user_by_id(db, id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        users_detail.append({"id": user.id, "email": user.email, "username": user.username})

    return users_detail