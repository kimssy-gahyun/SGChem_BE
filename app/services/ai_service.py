import ollama
from app.core.config import settings


def analyze_compatibility(user_bio: str, target_bio: str) -> dict:
    """두 유저의 자기소개를 기반으로 AI 궁합 분석"""
    prompt = f"""
당신은 소개팅 매칭 AI입니다. 두 사람의 자기소개를 보고 궁합을 분석해주세요.

사람 A: {user_bio}
사람 B: {target_bio}

다음 형식으로 분석해주세요:
1. 궁합 점수 (0~100)
2. 잘 맞는 점 (2~3가지)
3. 주의할 점 (1~2가지)
4. 한줄 총평
"""
    response = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"analysis": response["message"]["content"]}


def generate_icebreaker(user_bio: str, target_bio: str) -> str:
    """첫 대화 시작 문장 추천"""
    prompt = f"""
소개팅 앱에서 두 사람이 매칭되었습니다.

나: {user_bio}
상대: {target_bio}

자연스럽고 호감을 줄 수 있는 첫 메시지 3가지를 추천해주세요.
"""
    response = ollama.chat(
        model=settings.OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]
