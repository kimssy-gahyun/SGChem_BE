from math import sqrt
from sqlalchemy.orm import Session
from app.models.user import User, GenderEnum

VECTOR_KEYS = [
    "내향성", "논리적", "지적호기심", "독립성",
    "교감추구", "사회적에너지", "안정추구", "동성연애수용",
]

# 각 차원 값이 [0.2, 0.8] 범위라 최대 가능 거리 = sqrt(N * 0.6^2)
_MAX_EUCLIDEAN_DIST = sqrt(len(VECTOR_KEYS)) * 0.6


def _cosine_similarity(a: dict, b: dict) -> float:
    """두 성향 벡터의 코사인 유사도 (0~1)"""
    va = [a.get(k, 0.5) for k in VECTOR_KEYS]
    vb = [b.get(k, 0.5) for k in VECTOR_KEYS]
    dot = sum(x * y for x, y in zip(va, vb))
    na = sqrt(sum(x * x for x in va))
    nb = sqrt(sum(y * y for y in vb))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _euclidean_similarity(a: dict, b: dict) -> float:
    """유클리드 거리를 유사도로 변환 (0~1, 1에 가까울수록 비슷)"""
    va = [a.get(k, 0.5) for k in VECTOR_KEYS]
    vb = [b.get(k, 0.5) for k in VECTOR_KEYS]
    dist = sqrt(sum((x - y) ** 2 for x, y in zip(va, vb)))
    return max(0.0, 1.0 - dist / _MAX_EUCLIDEAN_DIST)


def _blended_similarity(a: dict, b: dict) -> float:
    """코사인 + 유클리드 5:5 블렌딩 (PoC 결과 기반, 보고서 §3.4)"""
    return 0.5 * _cosine_similarity(a, b) + 0.5 * _euclidean_similarity(a, b)


def get_candidates(db: Session, current_user: User, limit: int = 10) -> list[User]:
    """현재 유저와 반대 성별 후보 목록"""
    opposite = GenderEnum.female if current_user.gender == GenderEnum.male else GenderEnum.male
    return (
        db.query(User)
        .filter(User.id != current_user.id)
        .filter(User.gender == opposite)
        .limit(limit)
        .all()
    )


def get_candidates_with_scores(
    db: Session, current_user: User, limit: int = 20
) -> list[dict]:
    """반대 성별 후보 + 성향 유사도 점수. 점수 내림차순 정렬."""
    opposite = GenderEnum.female if current_user.gender == GenderEnum.male else GenderEnum.male
    candidates = (
        db.query(User)
        .filter(User.id != current_user.id)
        .filter(User.gender == opposite)
        .all()
    )

    my_vec = current_user.interview_vector or {}
    results = []
    for c in candidates:
        if not c.interview_vector:
            continue
        sim = _blended_similarity(my_vec, c.interview_vector) if my_vec else 0.0
        results.append({"user": c, "score": round(sim * 100)})

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]
