from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, date


class UserCreate(BaseModel):
    username: str
    nickname: str
    password: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    bio: Optional[str] = None


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    interview_vector: Optional[Dict[str, float]] = None
    interview_summary: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    interview_vector: Optional[Dict[str, float]] = None
    interview_summary: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
