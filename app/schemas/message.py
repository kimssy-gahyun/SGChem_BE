from datetime import datetime
from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
