from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm():
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3,
        max_tokens=512
    )

def expand_ingredients_prompt(ingredients):
    return f"""다음은 재료 목록입니다: {', '.join(ingredients)}.
이 재료들을 포함해 요리에 자주 함께 쓰이는 연관 재료들을 추천해 주세요.
결과는 쉼표로 구분해서 주세요."""

def smart_recommendation_prompt(ingredients, recipes):
    return f"""다음은 사용자가 가진 재료입니다: {', '.join(ingredients)}.
아래는 요리 레시피 후보 목록입니다: {', '.join(recipes)}.
사용자의 재료와 가장 잘 어울리는 레시피 하나를 추천하고, 그 이유를 간단히 설명해 주세요.
결과는 다음 형식으로 주세요:
레시피 이름
이유: 설명"""
