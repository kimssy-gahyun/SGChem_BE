from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services import matching_service, ai_service
from app.api.v1.users import get_current_user

router = APIRouter(prefix="/matching", tags=["matching"])


class CandidateWithScore(BaseModel):
    user: UserResponse
    score: int


@router.get("/candidates", response_model=list[CandidateWithScore])
def get_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return matching_service.get_candidates_with_scores(db, current_user, limit=6)


@router.get("/compatibility/{target_id}")
def get_compatibility(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="상대방을 찾을 수 없습니다.")
    if not current_user.interview_vector or not target.interview_vector:
        raise HTTPException(status_code=400, detail="AI 인터뷰를 먼저 완료해주세요.")

    me = {
        "nickname": current_user.nickname,
        "vector": current_user.interview_vector,
        "summary": current_user.interview_summary,
        "bio": current_user.bio,
    }
    other = {
        "nickname": target.nickname,
        "vector": target.interview_vector,
        "summary": target.interview_summary,
        "bio": target.bio,
    }
    return ai_service.analyze_compatibility(me, other)


@router.get("/icebreaker/{target_id}")
def get_icebreaker(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="상대방을 찾을 수 없습니다.")

    me = {
        "nickname": current_user.nickname,
        "bio": current_user.bio,
        "summary": current_user.interview_summary,
    }
    other = {
        "nickname": target.nickname,
        "bio": target.bio,
        "summary": target.interview_summary,
    }
    message = ai_service.generate_icebreaker(me, other)
    return {"suggestions": message}
