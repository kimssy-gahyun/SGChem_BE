from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.user import UserResponse


class ChatRoomResponse(BaseModel):
    partner: UserResponse
    created_at: datetime
    last_active_at: datetime
    unread_count: int = 0
    partner_last_read_at: Optional[datetime] = None  # 상대가 나와의 채팅을 마지막으로 읽은 시각

    model_config = {"from_attributes": True}
