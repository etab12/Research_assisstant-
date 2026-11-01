
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("QWEN_MODEL")

if not api_key:
    raise ValueError(
        "OPENROUTER_API_KEY is missing from your .env file."
    )

if not model or model == "qwen_model_id_from_openrouter":
    raise ValueError(
        "Set QWEN_MODEL to the exact model ID from OpenRouter."
    )

llm = ChatOpenAI(
    model=model,
    api_key=api_key,
    base_url=os.getenv(
        "OPENROUTER_BASE_URL",
        "https://openrouter.ai/api/v1",
    ),
    max_retries=3,
    timeout=60,
    temperature=0,
)
print(model)
