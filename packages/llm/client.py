from openai import OpenAI
from packages.core.config import settings

client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    timeout=settings.DEEPSEEK_API_TIMEOUT,
    )

