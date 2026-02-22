from fastapi import APIRouter
from app.api.v1.conversation_routes import router as conversation_router
from app.api.v1.message_routes import router as message_router
from app.api.v1.ws_routes import router as ws_router

router = APIRouter()

router.include_router(conversation_router)
router.include_router(message_router)
router.include_router(ws_router)
