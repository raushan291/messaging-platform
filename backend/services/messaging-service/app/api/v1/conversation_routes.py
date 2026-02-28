from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, aliased
from sqlalchemy.dialects.postgresql import UUID
import uuid
from http.client import HTTPException
from typing import List

from app.db.session import SessionLocal
from app.models.conversation import Conversation, ConversationType
from app.models.conversation_participant import ConversationParticipant
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from app.core.security import get_current_user_id
from app.core.http_rate_limit import user_rate_limit
from app.core.config import settings

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create Conversation
@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    # Rate limit
    await user_rate_limit(
        str(current_user_id),
        action="create_conversation",
        limit=settings.CREATE_CONVERSATION_LIMIT,
        window=settings.CREATE_CONVERSATION_WINDOW,
    )

    # Abuse prevention
    if len(payload.participant_ids) > settings.MAX_CONVERSATION_PARTICIPANTS:
        raise HTTPException(400, "Too many participants")

    # Remove duplicates
    participant_ids = set(payload.participant_ids)

    # Prevent user adding themselves manually
    participant_ids.discard(current_user_id)

    # Add creator
    participant_ids.add(current_user_id)

    if len(participant_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 participants required")

    # Decide conversation type
    if len(participant_ids) == 2:
        conversation_type = ConversationType.PRIVATE
    else:
        conversation_type = ConversationType.GROUP

    # Prevent duplicate private conversations
    if conversation_type == ConversationType.PRIVATE:
        user_list = list(participant_ids)

        cp1 = aliased(ConversationParticipant)
        cp2 = aliased(ConversationParticipant)

        existing = (
            db.query(Conversation).filter(Conversation.is_deleted == False)
            .join(cp1, Conversation.id == cp1.conversation_id)
            .join(cp2, Conversation.id == cp2.conversation_id)
            .filter(
                Conversation.type == ConversationType.PRIVATE,
                cp1.user_id == user_list[0],
                cp2.user_id == user_list[1],
            )
            .first()
        )

        if existing:
            return existing

    conversation = Conversation(type=conversation_type, name=payload.name if conversation_type == ConversationType.GROUP else None)

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # Add participants
    for user_id in participant_ids:
        db.add(
            ConversationParticipant(
                conversation_id=conversation.id,
                user_id=user_id,
            )
        )

    db.commit()

    participant_ids = (
        db.query(ConversationParticipant.user_id)
        .filter(ConversationParticipant.conversation_id == conversation.id)
        .all()
    )

    return ConversationResponse(
        id=conversation.id,
        type=conversation.type,
        name=conversation.name,
        created_at=conversation.created_at,
        participant_ids=[p[0] for p in participant_ids],
    )



@router.get("/", response_model=List[ConversationResponse])
async def get_my_conversations(
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # Rate limit
    await user_rate_limit(current_user_id, action="get_conversations", limit=settings.GET_CONVERSATION_LIMIT, window=settings.GET_CONVERSATION_WINDOW)

    conversations = (
        db.query(Conversation).filter(Conversation.is_deleted == False)
        .join(ConversationParticipant)
        .filter(ConversationParticipant.user_id == current_user_id)
        .all()
    )

    result = []
    for conv in conversations:
        participants = (
            db.query(ConversationParticipant.user_id)
            .filter(ConversationParticipant.conversation_id == conv.id)
            .all()
        )

        result.append({
            "id": conv.id,
            "type": conv.type,
            "name": conv.name,
            "created_at": conv.created_at,
            "participant_ids": [p.user_id for p in participants]
        })

    return result


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # Rate limit
    await user_rate_limit(current_user_id, action="update_conversation", limit=settings.UPDATE_CONVERSATION_LIMIT, window=settings.UPDATE_CONVERSATION_WINDOW)

    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.is_deleted == False).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.name = payload.name
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user_id)):
    # Rate limit
    await user_rate_limit(current_user_id, action="delete_conversation", limit=settings.DELETE_CONVERSATION_LIMIT, window=settings.DELETE_CONVERSATION_WINDOW)

    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.is_deleted == False).first()

    if not conv:
        raise HTTPException(404, "Conversation not found")

    conv.is_deleted = True
    conv.deleted_at = datetime.utcnow()

    db.commit()
    return {"status": "conversation deleted"}
