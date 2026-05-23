from fastapi import APIRouter
from app.api.v1 import auth, users, matching, chats, ws

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(matching.router)
router.include_router(chats.router)
router.include_router(ws.router)
