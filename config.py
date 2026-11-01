
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "research_results"
OUTPUT_DIR.mkdir(exist_ok=True)

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3.5-flash")

NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

MAX_PAPERS = 20
REQUEST_TIMEOUT = 30

if not QWEN_API_KEY:
    raise ValueError(
        "QWEN_API_KEY is missing. Add it to your .env file."
    )

if not NCBI_EMAIL:
    raise ValueError(
        "NCBI_EMAIL is missing. Add your email to .env."
    )
