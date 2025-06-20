from datetime import datetime

from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class UserCreate(BaseModel):
    username: constr(min_length=3)
    email: EmailStr
    password: constr(min_length=8)
    university: str
    semester: int
    mobile: str
    alt_mobile: Optional[str] = None

class UserVerify(BaseModel):
    mobile: str
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailRequest(BaseModel):
    email: str

class UserResponse(BaseModel):
    username: str
    email: EmailStr
    university: str
    semester: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    password: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class EmailUpdate(BaseModel):
    new_email: EmailStr
    current_password: str

class EmailSchema(BaseModel):
    email: str

class LoginMethod(BaseModel):
    email: EmailStr

class FaceLoginRequest(BaseModel):
    email: EmailStr
    face_data: str  # Base64 encoded image data

class FaceRegistrationRequest(BaseModel):
    email: EmailStr
    face_data: str  # Base64 encoded image data