from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from datetime import datetime

from app.db.session import SessionLocal
from app.models.message import Message
from app.models.conversation_participant import ConversationParticipant
from app.schemas.message import MessageCreate, MessageResponse
from app.core.security import get_current_user_id

router = APIRouter(prefix="/messages", tags=["Messages"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Send Message
@router.post("/", response_model=MessageResponse)
def send_message(
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # Check user is participant
    participant = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == payload.conversation_id,
            ConversationParticipant.user_id == current_user_id,
        )
        .first()
    )

    if not participant:
        raise HTTPException(status_code=403, detail="Not part of conversation")

    message = Message(
        conversation_id=payload.conversation_id,
        sender_id=current_user_id,
        content=payload.content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


# Get Messages of Conversation
@router.get("/{conversation_id}", response_model=List[MessageResponse])
def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # Ensure user is part of conversation
    participant = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user_id
        )
        .first()
    )

    if not participant:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.is_deleted == False)
        .order_by(Message.created_at.asc())
        .all()
    )

    result = []

    for msg in messages:
        reply_to = None

        if msg.reply_to_message_id:
            parent = (
                db.query(Message)
                .filter(Message.id == msg.reply_to_message_id, Message.is_deleted == False)
                .first()
            )

            if parent:
                reply_to = {
                    "id": str(parent.id),
                    "content": parent.content,
                    "sender_id": str(parent.sender_id),
                }

        result.append({
            "id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "sender_id": str(msg.sender_id),
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "reply_to_message_id": str(msg.reply_to_message_id) if msg.reply_to_message_id else None,
            "reply_to": reply_to,
        })

    return result

# Delete Message
@router.delete("/{message_id}")
def delete_message(message_id: str, db: Session = Depends(get_db), user_id=Depends(get_current_user_id)):
    msg = db.query(Message).filter(Message.id == message_id, Message.is_deleted == False).first()

    if not msg:
        raise HTTPException(404, "Message not found")
    
    # check user is part of the conversation
    is_participant = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == msg.conversation_id,
        ConversationParticipant.user_id == user_id
    ).first()

    if not is_participant:
        raise HTTPException(403, "Not allowed")

    msg.is_deleted = True
    msg.deleted_at = datetime.utcnow()

    db.commit()
    return {"status": "deleted"}
