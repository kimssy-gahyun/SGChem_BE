from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    nickname: str
    password: str
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
