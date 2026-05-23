import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.security import decode_token

router = APIRouter(prefix="/users", tags=["users"])
bearer = HTTPBearer()

UPLOAD_DIR = Path("uploads/profile_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/profile-image", response_model=UserResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="JPEG, PNG, GIF, WEBP 이미지만 업로드 가능합니다.")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="이미지는 5MB 이하만 업로드 가능합니다.")

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    new_name = f"{uuid.uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / new_name
    save_path.write_bytes(contents)

    # 이전 이미지 삭제 (uploads/ 안의 파일만)
    if current_user.profile_image and current_user.profile_image.startswith("/uploads/"):
        old_path = Path(current_user.profile_image.lstrip("/"))
        try:
            if old_path.exists() and old_path.is_relative_to(UPLOAD_DIR.parent):
                old_path.unlink()
        except (OSError, ValueError):
            pass

    current_user.profile_image = f"/uploads/profile_images/{new_name}"
    db.commit()
    db.refresh(current_user)
    return current_user
