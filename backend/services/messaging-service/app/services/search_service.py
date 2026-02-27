from elasticsearch import Elasticsearch
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

def index_message_from_event(event: dict):
    doc = {
        "id": event["id"],
        "conversation_id": event["conversation_id"],
        "sender_id": event["sender_id"],
        "content": event["content"],
        "created_at": event["created_at"],
        "reply_to_message_id": event.get("reply_to_message_id"),
        "reply_to": event.get("reply_to"),
        "is_deleted": event.get("is_deleted", False),
        "deleted_at": event.get("deleted_at"),
    }

    es.index(index=INDEX_NAME, id=doc["id"], document=doc)
