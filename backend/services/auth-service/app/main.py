from fastapi import FastAPI
from app.api.v1.auth_routes import router as auth_router
from app.api.v1.user_routes import router as user_router
from app.db.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware
import app.models

app = FastAPI(title="Auth Service", version="1.0.0")

# Create tables (dev only)
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "Auth service is running"}
