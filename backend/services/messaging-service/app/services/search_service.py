from elasticsearch import Elasticsearch
from fastapi import Depends
from app.models.message import Message
from app.db.session import SessionLocal
from app.core.config import settings


es = Elasticsearch(settings.ELASTICSEARCH_URL)

INDEX_NAME = "messages"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def index_message(message, db = Depends(get_db)):
    reply_to = None
    if message.reply_to_message_id:
        parent = (
            db.query(Message)
            .filter(Message.id == message.reply_to_message_id, Message.is_deleted == False)
            .first()
        )

        if parent:
            reply_to = {
                "id": str(parent.id),
                "content": parent.content,
                "sender_id": str(parent.sender_id),
            }
    doc = {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "sender_id": str(message.sender_id),
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "reply_to_message_id": str(message.reply_to_message_id) if message.reply_to_message_id else None,
        "reply_to": reply_to,
        "is_deleted": message.is_deleted,
        "deleted_at": message.deleted_at.isoformat() if message.deleted_at else None,
    }

    es.index(index=INDEX_NAME, id=str(message.id), document=doc)
