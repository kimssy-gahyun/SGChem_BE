from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Enum, JSON
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    gender = Column(Enum(GenderEnum), nullable=True)
    birth_date = Column(Date, nullable=True)
    bio = Column(Text, nullable=True)
    profile_image = Column(String(500), nullable=True)
    interview_vector = Column(JSON, nullable=True)
    interview_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
