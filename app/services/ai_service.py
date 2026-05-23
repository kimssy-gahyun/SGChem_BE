import ollama
from app.core.config import settings


def _format_user(label: str, data: dict) -> str:
    """이름은 의도적으로 제외 — LLM이 평가문에 이름을 인용하지 않게."""
    parts = [f"[{label}]"]
    if data.get("summary"):
        parts.append(f"성향 요약: {data['summary']}")
    if data.get("bio"):
        parts.append(f"자기소개: {data['bio']}")
    if data.get("vector"):
        parts.append("성향 점수:")
        for k, v in data["vector"].items():
            level = "높음" if v >= 0.7 else "낮음" if v <= 0.3 else "보통"
            parts.append(f"  - {k}: {level}")
    return "\n".join(parts)


def analyze_compatibility(user_a: dict, user_b: dict) -> dict:
    """두 유저의 성향을 기반으로 AI 궁합 분석 — 한 줄 총평만 반환"""
    prompt = (
        "두 사람의 성향 정보를 보고 소개팅 궁합을 한국어로 한 두 문장 평가해줘.\n\n"
        f"{_format_user('사람 A', user_a)}\n\n"
        f"{_format_user('사람 B', user_b)}\n\n"
        "조건:\n"
        "- 두 사람의 성향을 비교한 결과를 자연스럽게 풀어쓰기.\n"
        "- 이름·닉네임·'A', 'B', '사람 A', '사람 B' 같은 라벨 절대 언급 금지. "
        "주어 없이 '서로~', '두 분~' 같은 표현으로 자연스럽게 표현.\n"
        "- 마크다운·번호·글머리표·이모지·따옴표·헤더(##, **) 모두 금지.\n"
        "- 부연 설명·전제·접두어 없이 평가 문장만 출력."
    )
    response = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.5, "top_p": 0.9, "repeat_penalty": 1.2},
    )
    return {"analysis": response["message"]["content"].strip()}


def generate_icebreaker(user_a: dict, user_b: dict) -> str:
    """첫 대화 시작 문장 3가지 추천"""
    def fmt(label, data):
        parts = [f"[{label}]"]
        if data.get("nickname"):
            parts.append(f"이름: {data['nickname']}")
        if data.get("bio"):
            parts.append(f"자기소개: {data['bio']}")
        if data.get("summary"):
            parts.append(f"성향: {data['summary']}")
        return "\n".join(parts)

    prompt = (
        "소개팅 앱에서 두 사람이 매칭됐어. 내가 상대에게 보낼 "
        "첫 인사 메시지 2가지를 한국어로 추천해줘.\n\n"
        f"{fmt('나', user_a)}\n\n"
        f"{fmt('상대', user_b)}\n\n"
        "규칙:\n"
        "- 2개를 줄바꿈으로 구분해서 출력. 각 메시지는 한 문장, 길어도 두 문장까지.\n"
        "- 카톡 첫 메시지처럼 부담 없고 짧은 구어체.\n"
        "- 1번: 반드시 '안녕하세요' 또는 '반가워요' 둘 중 하나가 포함된 짧은 인사 한 줄. "
        "예: '안녕하세요 반가워요!', '안녕하세요~ 매칭됐네요 ㅎㅎ'. "
        "이름·자기소개 언급하지 말고 인사만.\n"
        "- 2번: 상대 자기소개나 성향에서 자연스럽게 한 가지 꺼내서 가벼운 질문 던지기.\n"
        "- 번호·글머리표·마크다운 금지. 이모지는 자유.\n"
        "- 이름·닉네임 절대 언급 금지. '○○님', '저는 ○○입니다' 같은 표현 모두 금지.\n"
        "- 부연 설명·전제·접두어 없이 메시지 2줄만."
    )
    response = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.7, "top_p": 0.9},
    )
    return response["message"]["content"].strip()
