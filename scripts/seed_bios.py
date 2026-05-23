"""interview_vector 기반으로 사용자의 1인칭 자기소개(bio)를 LLM으로 생성한다.

bio가 비어있는 유저만 채워 넣는다.
실행: cd C:\\SG\\SGChem_BE && .venv\\Scripts\\python.exe scripts/seed_bios.py
"""
import sys
import time
import ollama

sys.path.insert(0, '.')
from app.db.database import SessionLocal
from app.models.user import User

MODEL = "exaone3.5:7.8b"

DISPLAY_LABELS = {
    "내향성": "내향성",
    "논리적": "논리적 사고",
    "지적호기심": "지적 호기심",
    "독립성": "독립성",
    "교감추구": "교감 추구",
    "사회적에너지": "사회적 에너지",
    "안정추구": "안정 추구",
    "동성연애수용": "다양성 수용",
}


def build_prompt(vector: dict) -> str:
    score_lines = []
    for key, label in DISPLAY_LABELS.items():
        val = vector.get(key, 0.5)
        level = "높음" if val >= 0.7 else "낮음" if val <= 0.3 else "보통"
        score_lines.append(f"- {label}: {level}")
    return (
        "아래 성향 점수를 가진 사람이 소개팅 앱에 올릴 1인칭 자기소개를 한국어로 한두 문장 작성해줘.\n\n"
        "조건:\n"
        "- 1인칭 시점, 친근한 구어체 (반말 아님, 존댓말 또는 평어). "
        "예: '~ 좋아해요', '~ 편이에요'.\n"
        "- 한두 문장으로 짧게. 너무 진지하거나 형식적이지 않게.\n"
        "- 성향이 자연스럽게 묻어나도록.\n"
        "- 마크다운·번호·이모지 금지.\n"
        "- 자기소개 문장만 출력. 부연·접두어·따옴표 모두 금지.\n\n"
        "[성향]\n"
        + "\n".join(score_lines)
    )


def generate_bio(vector: dict) -> str:
    res = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": build_prompt(vector)}],
        options={"temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.2},
    )
    bio = res["message"]["content"].strip()
    # 따옴표·접두어 살짝 청소
    bio = bio.strip('"').strip("'").strip()
    return bio


def main():
    db = SessionLocal()
    targets = (
        db.query(User)
        .filter(User.interview_vector.isnot(None))
        .filter((User.bio.is_(None)) | (User.bio == ""))
        .order_by(User.id)
        .all()
    )
    total = len(targets)
    print(f"대상: {total}명 (bio 비어있는 유저)", flush=True)

    start = time.time()
    for i, u in enumerate(targets, 1):
        t0 = time.time()
        try:
            b = generate_bio(u.interview_vector)
            u.bio = b
            db.commit()
            print(f"[{i}/{total}] {u.username} ({u.nickname}) - {time.time()-t0:.1f}s", flush=True)
            print(f"    → {b[:90]}{'...' if len(b) > 90 else ''}", flush=True)
        except Exception as e:
            db.rollback()
            print(f"[{i}/{total}] {u.username} 실패: {e}", flush=True)

    db.close()
    print(f"\n완료. 전체 소요: {time.time()-start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
