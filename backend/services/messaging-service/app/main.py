from fastapi import FastAPI
from app.db.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as api_router
from app.api.v1.ws_routes import router as ws_router
import app.models

app = FastAPI(title="Messaging Service", version="1.0.0")

# Create tables (dev only)
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1") 

@app.get("/health")
def health():
    return {"status": "Messaging service is running"}
