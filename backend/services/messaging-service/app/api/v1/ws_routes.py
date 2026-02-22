from fastapi import WebSocket, APIRouter
from app.core.jwt import verify_token
from app.services.websocket_manager import manager
from app.models.message import Message
from app.db.session import SessionLocal

router = APIRouter()


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_endpoint(ws: WebSocket, conversation_id: str):
    token = ws.query_params.get("token")
    user_id = verify_token(token)

    if not user_id:
        await ws.close()
        return

    await manager.connect(conversation_id, ws)

    db = SessionLocal()

    try:
        while True:
            data = await ws.receive_json()

            message = Message(
                conversation_id=conversation_id,
                sender_id=user_id,
                content=data["content"],
                reply_to_message_id=data.get("reply_to_message_id"),
            )

            db.add(message)
            db.commit()
            db.refresh(message)

            reply_to = None

            if message.reply_to_message_id:
                parent = db.query(Message).filter(
                    Message.id == message.reply_to_message_id
                ).first()

                if parent:
                    reply_to = {
                        "id": str(parent.id),
                        "content": parent.content,
                        "sender_id": str(parent.sender_id),
                    }

            await manager.broadcast(
                conversation_id,
                {
                    "id": str(message.id),
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "reply_to_message_id": str(message.reply_to_message_id) if message.reply_to_message_id else None,
                    "reply_to": reply_to,
                    "is_deleted": message.is_deleted,
                    "deleted_at": message.deleted_at.isoformat() if message.deleted_at else None,
                }
            )

    except Exception:
        manager.disconnect(conversation_id, ws)
