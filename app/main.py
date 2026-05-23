from pathlib import Path
from sqlalchemy import text
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.router import router
from app.db.database import Base, engine
# 모델 로드 (create_all 이전에 import 되어야 테이블 생성됨)
from app.models import user, chat_room, message  # noqa: F401

Base.metadata.create_all(bind=engine)

# SQLite 기존 DB에 누락된 컬럼 보강 / 컬럼 마이그레이션 (개발용 간이 마이그레이션)
def _ensure_columns():
    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
        if "interview_vector" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN interview_vector JSON"))
        if "email" in cols and "username" not in cols:
            conn.execute(text("ALTER TABLE users RENAME COLUMN email TO username"))
            conn.execute(text(
                "UPDATE users SET username = substr(username, 1, instr(username, '@') - 1) "
                "WHERE instr(username, '@') > 0"
            ))
        if "birth_date" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN birth_date DATE"))
        if "interview_summary" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN interview_summary TEXT"))

        # chat_rooms.last_read_at 컬럼 추가
        cr_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(chat_rooms)")).fetchall()}
        if cr_cols and "last_read_at" not in cr_cols:
            conn.execute(text("ALTER TABLE chat_rooms ADD COLUMN last_read_at DATETIME"))
            conn.execute(text("UPDATE chat_rooms SET last_read_at = created_at WHERE last_read_at IS NULL"))
        # 재조회 (방금 추가한 컬럼 포함)
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()}
        if "age" in cols:
            conn.execute(text("ALTER TABLE users DROP COLUMN age"))

if engine.url.get_backend_name() == "sqlite":
    _ensure_columns()

app = FastAPI(title="SGChem API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
