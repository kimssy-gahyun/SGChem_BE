"""실시간 채팅 WebSocket — DB에 영구 저장 + 온라인 유저에게 실시간 relay."""
import time
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_token
from app.db.database import SessionLocal
from app.models.message import Message
from app.models.chat_room import ChatRoom


def _utc_now():
    return datetime.now(timezone.utc)

router = APIRouter()


class ConnectionManager:
    """user_id → list[WebSocket] 매핑. 동일 유저가 여러 탭/기기로 동시 접속 가능."""
    def __init__(self):
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(user_id, []).append(ws)

    def disconnect(self, user_id: int, ws: WebSocket):
        conns = self.active.get(user_id)
        if not conns:
            return
        try:
            conns.remove(ws)
        except ValueError:
            pass
        if not conns:
            self.active.pop(user_id, None)

    async def send_to(self, target_id: int, payload: dict) -> bool:
        """타겟 유저의 모든 활성 세션에 broadcast. 하나라도 성공하면 True."""
        conns = self.active.get(target_id)
        if not conns:
            return False
        dead = []
        delivered = False
        for ws in list(conns):
            try:
                await ws.send_json(payload)
                delivered = True
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                conns.remove(ws)
            except ValueError:
                pass
        if not conns:
            self.active.pop(target_id, None)
        return delivered


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def chat_ws(ws: WebSocket, token: str = Query(...)):
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await ws.close(code=4401)
        return

    await manager.connect(user_id, ws)
    try:
        while True:
            data = await ws.receive_json()

            # 타이핑 신호 — 저장하지 않고 그대로 상대에게 전달
            if data.get("type") == "typing":
                try:
                    to = int(data.get("to"))
                except (TypeError, ValueError):
                    continue
                if to == user_id:
                    continue
                await manager.send_to(to, {"type": "typing", "from": user_id})
                continue

            try:
                to = int(data.get("to"))
                text = str(data.get("text", "")).strip()
            except (TypeError, ValueError):
                continue
            if not text or to == user_id:
                continue

            # DB 저장 + 양쪽 chat_rooms upsert (수신자도 사이드바에 방이 보이게)
            db = SessionLocal()
            try:
                now = _utc_now()
                msg = Message(
                    sender_id=user_id,
                    recipient_id=to,
                    content=text,
                    created_at=now,
                )
                db.add(msg)

                for owner, partner in ((user_id, to), (to, user_id)):
                    room = (
                        db.query(ChatRoom)
                        .filter(ChatRoom.user_id == owner, ChatRoom.partner_id == partner)
                        .first()
                    )
                    if room:
                        room.last_active_at = now
                    else:
                        db.add(ChatRoom(
                            user_id=owner,
                            partner_id=partner,
                            created_at=now,
                            last_active_at=now,
                            last_read_at=now,
                        ))

                db.commit()
                db.refresh(msg)
                ts_ms = int(now.timestamp() * 1000)
                msg_id = msg.id
            finally:
                db.close()

            payload = {
                "id": msg_id,
                "from": user_id,
                "to": to,
                "text": text,
                "ts": ts_ms,
            }
            # 1. 상대 유저의 모든 활성 세션에 relay
            delivered = await manager.send_to(to, payload)

            # 2. 송신자의 '다른' 세션들에도 echo (현재 ws 제외) — multi-tab 동기화
            for other_ws in list(manager.active.get(user_id, [])):
                if other_ws is ws:
                    continue
                try:
                    await other_ws.send_json(payload)
                except Exception:
                    pass

            # 3. 송신자에게 ACK
            try:
                await ws.send_json({
                    "ack": True,
                    "id": msg_id,
                    "to": to,
                    "delivered": delivered,
                    "text": text,
                    "ts": ts_ms,
                })
            except Exception:
                break
    except WebSocketDisconnect:
        manager.disconnect(user_id, ws)
    except Exception:
        manager.disconnect(user_id, ws)
        try:
            await ws.close()
        except Exception:
            pass
