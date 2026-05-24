from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from datetime import datetime, date
from app.models.user import GenderEnum


# 8차원 성향 벡터 키 (FE Interview.jsx VECTOR_LABELS와 일치)
ALLOWED_VECTOR_KEYS = {
    "내향성", "논리적", "지적호기심", "독립성",
    "교감추구", "사회적에너지", "안정추구", "동성연애수용",
}


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    nickname: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=6, max_length=128)
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    bio: Optional[str] = Field(default=None, max_length=500)

    @field_validator("nickname")
    @classmethod
    def nickname_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("이름은 공백만으로 구성될 수 없습니다.")
        return v


class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=2, max_length=20)
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    bio: Optional[str] = Field(default=None, max_length=500)
    profile_image: Optional[str] = None
    interview_vector: Optional[Dict[str, float]] = None
    interview_summary: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("interview_vector")
    @classmethod
    def vector_must_match_schema(cls, v):
        if v is None:
            return v
        invalid_keys = set(v.keys()) - ALLOWED_VECTOR_KEYS
        if invalid_keys:
            raise ValueError(f"허용되지 않은 성향 키: {sorted(invalid_keys)}")
        for k, val in v.items():
            if not (0.0 <= float(val) <= 1.0):
                raise ValueError(f"성향 값은 0~1 사이여야 합니다: {k}={val}")
        return v


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
