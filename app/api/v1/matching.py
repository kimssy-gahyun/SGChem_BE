from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services import matching_service, ai_service
from app.api.v1.users import get_current_user

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/candidates", response_model=list[UserResponse])
def get_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return matching_service.get_candidates(db, current_user)


@router.get("/compatibility/{target_id}")
def get_compatibility(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="상대방을 찾을 수 없습니다.")
    if not current_user.bio or not target.bio:
        raise HTTPException(status_code=400, detail="자기소개를 먼저 작성해주세요.")

    result = ai_service.analyze_compatibility(current_user.bio, target.bio)
    return result


@router.get("/icebreaker/{target_id}")
def get_icebreaker(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="상대방을 찾을 수 없습니다.")

    message = ai_service.generate_icebreaker(
        current_user.bio or "", target.bio or ""
    )
    return {"suggestions": message}
