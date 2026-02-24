import os
from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()

ai_token = os.getenv("OPEN_AI")


client = AsyncOpenAI(
    api_key=ai_token,
    base_url="https://openrouter.ai/api/v1",
    timeout=30.0,
    max_retries=2
)

async def ask_chat_gpt(request: str) -> str:
    try:
        request = request[:10000]
        
        response = await client.chat.completions.create(  # <-- ВАЖНО: используем chat.completions
            model="google/gemini-3-flash-preview",  # <-- ПРАВИЛЬНОЕ имя модели
            messages=[
                {"role": "user", "content": request}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        if not result:
            return "🤔 Gemini вернул пустой ответ."
        
        return result
        
    except Exception as e:
        print(f"OpenAI SDK error: {e}")
        return f"❌ Ошибка: {str(e)[:100]}"



