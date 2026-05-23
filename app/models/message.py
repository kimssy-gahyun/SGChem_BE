from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from app.db.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    # SQLite CURRENT_TIMESTAMP는 초 단위라 ms 정밀도 위해 Python datetime 사용
    created_at = Column(DateTime(timezone=True), default=_utc_now, nullable=False)

    # 두 유저 간 대화 조회를 위한 복합 인덱스
    __table_args__ = (
        Index("ix_messages_pair", "sender_id", "recipient_id", "created_at"),
    )
