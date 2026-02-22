from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken

def save_refresh_token(db: Session, token: RefreshToken):
    db.add(token)
    db.commit()

def get_refresh_token(db: Session, token: str):
    return db.query(RefreshToken)\
        .filter(
            RefreshToken.token == token,
            RefreshToken.revoked == False
        ).first()

def revoke_refresh_token(db: Session, token: RefreshToken):
    if not token.revoked:
        token.revoked = True
        db.commit()
