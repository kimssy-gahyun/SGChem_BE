from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

MIN_AGE = 19


@router.get("/check-username")
def check_username(username: str, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == username).first() is not None
    return {"available": not exists}


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

    if body.birth_date:
        today = date.today()
        age = today.year - body.birth_date.year - (
            (today.month, today.day) < (body.birth_date.month, body.birth_date.day)
        )
        if age < MIN_AGE:
            raise HTTPException(status_code=400, detail=f"만 {MIN_AGE}세 이상만 가입할 수 있습니다.")

    user = User(
        username=body.username,
        nickname=body.nickname,
        hashed_password=hash_password(body.password),
        gender=body.gender,
        birth_date=body.birth_date,
        bio=body.bio,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}
