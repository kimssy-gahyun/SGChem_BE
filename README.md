# SGChem Backend 🔧

> FastAPI 기반 회원 / 매칭 / 채팅 백엔드

---

## 🚀 빠른 시작

전제: **Python 3.12** 설치 (`py -3.12` 호출 가능해야 함)

```bash
# 1. 가상환경 생성
py -3.12 -m venv .venv

# 2. 활성화
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 서버 실행
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

기본 포트: **8000**. API 문서: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ⚙️ 환경설정

`.env` 파일이 레포에 포함되어 있어요. (개발 편의용)

```env
DATABASE_URL=sqlite:///./sgchem.db
SECRET_KEY=sgchem-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=exaone3.5:7.8b
CORS_ORIGINS=http://localhost:5173
```

**Ollama 설치 필요**:

```bash
ollama pull exaone3.5:7.8b
ollama serve   # (자동 실행되지 않으면)
```

---

## 💾 데이터베이스

`sgchem.db` (SQLite) 가 레포에 포함되어 있어요. 50명 더미 회원 + 인터뷰 결과 들어있음.

| 계정 | 비번 |
| --- | --- |
| `user01` ~ `user50` | `pass01` ~ `pass50` |

테이블 구조:
- `users` (회원 + 8차원 성향 벡터 + 자연어 요약)
- `chat_rooms` (채팅방 메타 + last_read_at)
- `messages` (채팅 메시지 본문)

---

## 🛡️ 입력 검증

**회원가입** (`POST /auth/register`):
- 아이디 3~30자, 닉네임 2~20자 (공백만 불가), 비밀번호 6~128자
- 성별: `male` / `female` / `other` 만 허용
- 생년월일: **만 19세 이상**만 가입 가능

**내 정보 수정** (`PATCH /users/me`):
- `interview_vector` 키 화이트리스트 (8차원만 허용):
  `내향성`, `논리적`, `지적호기심`, `독립성`, `교감추구`, `사회적에너지`, `안정추구`, `동성연애수용`
- 각 값은 0~1 범위 강제
- 임의 키/범위 초과 시 422 반환

---

## 📡 주요 엔드포인트

| 엔드포인트 | 설명 |
| --- | --- |
| `POST /api/v1/auth/register` | 회원가입 |
| `POST /api/v1/auth/login` | 로그인 (JWT) |
| `GET /api/v1/auth/check-username` | 아이디 중복 확인 |
| `GET /api/v1/users/me` | 내 정보 |
| `PATCH /api/v1/users/me` | 내 정보 수정 (bio, vector, summary 등) |
| `POST /api/v1/users/me/profile-image` | 프로필 사진 업로드 |
| `GET /api/v1/matching/candidates` | 매칭 후보 6명 (점수순) |
| `GET /api/v1/matching/compatibility/{id}` | 궁합 한줄 분석 (LLM) |
| `GET /api/v1/matching/icebreaker/{id}` | 첫 인사 추천 (LLM) |
| `GET /api/v1/chats` | 내 채팅방 목록 (unread 포함) |
| `POST /api/v1/chats/{partner_id}` | 채팅방 생성/touch |
| `POST /api/v1/chats/{partner_id}/read` | 채팅방 읽음 처리 |
| `GET /api/v1/chats/{partner_id}/messages` | 메시지 조회 |
| `WS /api/v1/ws/chat?token=...` | 실시간 채팅 WebSocket |
| `GET /uploads/profile_images/{file}` | 정적 이미지 |

---

## 🧰 폴더 구조

```
app/
├── main.py             # FastAPI 진입점 (CORS, StaticFiles, migration)
├── core/
│   ├── config.py       # .env 로딩 (pydantic-settings)
│   └── security.py     # JWT + bcrypt
├── db/database.py      # SQLAlchemy engine/session
├── models/             # User, ChatRoom, Message
├── schemas/            # Pydantic 스키마
├── services/
│   ├── ai_service.py   # LLM 호출 (궁합 분석, 아이스브레이커)
│   └── matching_service.py  # 코사인+유클리드 5:5 블렌딩
└── api/v1/             # 라우트 모듈들 (auth/users/matching/chats/ws)

scripts/                # 더미 데이터 시드 스크립트들
uploads/profile_images/ # 업로드된 프로필 이미지
```
