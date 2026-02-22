from pydantic import BaseModel, EmailStr

# login request schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# token response schema
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# register request schema
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
