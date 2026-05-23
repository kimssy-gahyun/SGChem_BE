"""기존 유저들의 interview_vector를 기반으로 interview_summary를 LLM으로 채워 넣는다.

실행: cd C:\\SG\\SGChem_BE && .venv\\Scripts\\python.exe scripts/seed_summaries.py
"""
import sys
import time
import ollama

# BE 패키지 import (스크립트가 SGChem_BE 루트에서 실행된다고 가정)
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
        "아래는 한 사람의 대화 성향 분석 결과야. 이 결과를 바탕으로 "
        "이 사람의 대화 스타일과 성향을 자연스러운 한국어로 한두 문장으로 요약해줘. "
        "판단·평가 어투 금지, 부드럽고 중립적인 어조로. "
        "예시) '대화를 적극적으로 이어가며, 유머와 공감 중심의 대화를 선호하는 경향이 있다.'\n\n"
        "[성향 분석 결과]\n"
        + "\n".join(score_lines)
        + "\n\n요약 문장만 출력해. 다른 설명·전제·접두어 모두 금지."
    )


def summarize(vector: dict) -> str:
    prompt = build_prompt(vector)
    res = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.4, "top_p": 0.9, "repeat_penalty": 1.2},
    )
    return res["message"]["content"].strip()


def main():
    db = SessionLocal()
    targets = (
        db.query(User)
        .filter(User.interview_vector.isnot(None))
        .filter(User.interview_summary.is_(None))
        .order_by(User.id)
        .all()
    )
    total = len(targets)
    print(f"대상: {total}명", flush=True)

    start = time.time()
    for i, u in enumerate(targets, 1):
        t0 = time.time()
        try:
            s = summarize(u.interview_vector)
            u.interview_summary = s
            db.commit()
            print(f"[{i}/{total}] {u.username} ({u.nickname}) - {time.time()-t0:.1f}s", flush=True)
            print(f"    → {s[:80]}{'...' if len(s) > 80 else ''}", flush=True)
        except Exception as e:
            db.rollback()
            print(f"[{i}/{total}] {u.username} 실패: {e}", flush=True)

    db.close()
    print(f"\n완료. 전체 소요: {time.time()-start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
