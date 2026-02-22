import uuid
import enum
from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from app.db.session import Base

class ConversationType(str, enum.Enum):
    PRIVATE = "private"
    GROUP = "group"

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)  # direct / group
    name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    participant_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
