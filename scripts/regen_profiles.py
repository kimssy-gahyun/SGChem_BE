"""모든 사용자의 interview_vector를 랜덤으로 새로 섞고, summary+bio도 LLM으로 재생성한다."""
import sys
import time
import random
import ollama

sys.path.insert(0, '.')
from app.db.database import SessionLocal
from app.models.user import User

MODEL = "exaone3.5:7.8b"

KEYS = ['내향성', '논리적', '지적호기심', '독립성', '교감추구', '사회적에너지', '안정추구', '동성연애수용']
LEVELS = [0.2, 0.5, 0.8]

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


def score_lines(vector):
    lines = []
    for key, label in DISPLAY_LABELS.items():
        val = vector.get(key, 0.5)
        level = "높음" if val >= 0.7 else "낮음" if val <= 0.3 else "보통"
        lines.append(f"- {label}: {level}")
    return "\n".join(lines)


def gen_summary(vector):
    prompt = (
        "아래는 한 사람의 대화 성향 분석 결과야. 이 결과를 바탕으로 "
        "이 사람의 대화 스타일과 성향을 자연스러운 한국어로 한두 문장으로 요약해줘. "
        "판단·평가 어투 금지, 부드럽고 중립적인 어조로. "
        "예시) '대화를 적극적으로 이어가며, 유머와 공감 중심의 대화를 선호하는 경향이 있다.'\n\n"
        "[성향 분석 결과]\n"
        + score_lines(vector)
        + "\n\n요약 문장만 출력해. 다른 설명·전제·접두어 모두 금지."
    )
    r = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.4, "top_p": 0.9, "repeat_penalty": 1.2},
    )
    return r["message"]["content"].strip()


def gen_bio(vector):
    prompt = (
        "아래 성향 점수를 가진 사람이 소개팅 앱에 올릴 1인칭 자기소개를 한국어로 한두 문장 작성해줘.\n\n"
        "조건:\n"
        "- 1인칭 시점, 친근한 구어체 (반말 아님, 존댓말 또는 평어). "
        "예: '~ 좋아해요', '~ 편이에요'.\n"
        "- 한두 문장으로 짧게. 너무 진지하거나 형식적이지 않게.\n"
        "- 성향이 자연스럽게 묻어나도록.\n"
        "- 마크다운·번호·이모지 금지.\n"
        "- 자기소개 문장만 출력. 부연·접두어·따옴표 모두 금지.\n\n"
        "[성향]\n"
        + score_lines(vector)
    )
    r = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.2},
    )
    return r["message"]["content"].strip().strip('"').strip("'").strip()


def main():
    random.seed(7777)
    db = SessionLocal()
    users = db.query(User).order_by(User.id).all()
    total = len(users)
    print(f"대상: {total}명", flush=True)

    start = time.time()
    for i, u in enumerate(users, 1):
        # 1. 새 벡터
        vec = {k: random.choice(LEVELS) for k in KEYS}
        u.interview_vector = vec

        # 2. summary 재생성
        t0 = time.time()
        try:
            u.interview_summary = gen_summary(vec)
        except Exception as e:
            print(f"  summary 실패 ({u.username}): {e}", flush=True)
            u.interview_summary = None

        # 3. bio 재생성
        try:
            u.bio = gen_bio(vec)
        except Exception as e:
            print(f"  bio 실패 ({u.username}): {e}", flush=True)

        db.commit()
        print(f"[{i}/{total}] {u.username} ({u.nickname}) - {time.time()-t0:.1f}s", flush=True)
        print(f"    summary: {(u.interview_summary or '')[:80]}", flush=True)
        print(f"    bio:     {(u.bio or '')[:80]}", flush=True)

    db.close()
    print(f"\n완료. 전체 소요: {time.time()-start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
