from sqlalchemy.orm import Session
from app.models.user import User, GenderEnum


def get_candidates(db: Session, current_user: User, limit: int = 10) -> list[User]:
    """현재 유저와 반대 성별 유저 목록 반환 (간단한 매칭 로직)"""
    opposite = GenderEnum.female if current_user.gender == GenderEnum.male else GenderEnum.male

    candidates = (
        db.query(User)
        .filter(User.id != current_user.id)
        .filter(User.gender == opposite)
        .limit(limit)
        .all()
    )
    return candidates
