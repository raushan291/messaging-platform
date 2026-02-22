from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MessageCreate(BaseModel):
    conversation_id: UUID
    content: str
    reply_to_message_id: UUID | None = None

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime
    reply_to_message_id: UUID | None = None
    reply_to: dict | None = None

    class Config:
        from_attributes = True
