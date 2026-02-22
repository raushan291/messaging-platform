from pydantic import BaseModel
from uuid import UUID
from typing import List
from datetime import datetime

class ConversationCreate(BaseModel):
    participant_ids: List[UUID]
    name: str | None = None

class ConversationResponse(BaseModel):
    id:UUID
    type:str
    name: str | None = None
    created_at: datetime
    participant_ids: List[UUID]

    class Config:
        from_attributes = True

class ConversationUpdate(BaseModel):
    name: str | None = None
