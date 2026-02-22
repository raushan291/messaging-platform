from pydantic import BaseModel, EmailStr
from uuid import UUID

# user response schema
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    is_active: bool

    class Config:
        from_attributes = True
