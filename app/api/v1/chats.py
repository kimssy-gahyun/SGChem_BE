from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.models.chat_room import ChatRoom
from app.models.message import Message
from app.schemas.chat_room import ChatRoomResponse
from app.schemas.message import MessageResponse
from app.api.v1.users import get_current_user

router = APIRouter(prefix="/chats", tags=["chats"])


def _utc_now():
    return datetime.now(timezone.utc)


@router.get("", response_model=list[ChatRoomResponse])
def list_my_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rooms = (
        db.query(ChatRoom)
        .filter(ChatRoom.user_id == current_user.id)
        .order_by(ChatRoom.last_active_at.desc())
        .all()
    )

    # 각 방의 unread_count = last_read_at 이후 상대가 보낸 메시지 수
    # partner_last_read_at = 상대가 나와의 채팅을 마지막으로 읽은 시각 (상대 시점의 last_read_at)
    result = []
    for r in rooms:
        unread = (
            db.query(Message)
            .filter(
                Message.sender_id == r.partner_id,
                Message.recipient_id == current_user.id,
                Message.created_at > r.last_read_at,
            )
            .count()
        ) if r.last_read_at else (
            db.query(Message)
            .filter(
                Message.sender_id == r.partner_id,
                Message.recipient_id == current_user.id,
            )
            .count()
        )
        # 상대 쪽 chat_room 조회
        partner_room = (
            db.query(ChatRoom)
            .filter(ChatRoom.user_id == r.partner_id, ChatRoom.partner_id == current_user.id)
            .first()
        )
        result.append({
            "partner": r.partner,
            "created_at": r.created_at,
            "last_active_at": r.last_active_at,
            "unread_count": unread,
            "partner_last_read_at": partner_room.last_read_at if partner_room else None,
        })
    return result


@router.post("/{partner_id}/read", status_code=204)
async def mark_as_read(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """해당 채팅방을 '지금 읽음'으로 표시 + 상대에게 WS read 신호 전송."""
    room = (
        db.query(ChatRoom)
        .filter(ChatRoom.user_id == current_user.id, ChatRoom.partner_id == partner_id)
        .first()
    )
    if room:
        room.last_read_at = _utc_now()
        db.commit()

        # 상대에게 read 신호 (송신자가 자기 메시지의 "1" 표시를 지울 수 있게)
        from app.api.v1.ws import manager
        import time
        await manager.send_to(partner_id, {
            "type": "read",
            "from": current_user.id,  # 읽은 사람 (= 송신자의 상대)
            "ts": int(time.time() * 1000),
        })
    return


@router.post("/{partner_id}", response_model=ChatRoomResponse)
def create_or_touch_room(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if partner_id == current_user.id:
        raise HTTPException(status_code=400, detail="본인과 채팅방을 만들 수 없습니다.")

    partner = db.query(User).filter(User.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="상대방을 찾을 수 없습니다.")

    room = (
        db.query(ChatRoom)
        .filter(ChatRoom.user_id == current_user.id, ChatRoom.partner_id == partner_id)
        .first()
    )
    if room:
        room.last_active_at = _utc_now()
    else:
        now = _utc_now()
        room = ChatRoom(
            user_id=current_user.id,
            partner_id=partner_id,
            created_at=now,
            last_active_at=now,
            last_read_at=now,
        )
        db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/{partner_id}/messages", response_model=list[MessageResponse])
def get_messages(
    partner_id: int,
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """나와 partner 간의 대화 메시지를 최근순으로 limit 개 가져온 뒤 시간 오름차순으로 반환."""
    me_id = current_user.id
    rows = (
        db.query(Message)
        .filter(
            or_(
                and_(Message.sender_id == me_id, Message.recipient_id == partner_id),
                and_(Message.sender_id == partner_id, Message.recipient_id == me_id),
            )
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()  # 시간 오름차순
    return rows


@router.delete("/{partner_id}", status_code=204)
def delete_room(
    partner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = (
        db.query(ChatRoom)
        .filter(ChatRoom.user_id == current_user.id, ChatRoom.partner_id == partner_id)
        .first()
    )
    if room:
        db.delete(room)
        db.commit()
    return
