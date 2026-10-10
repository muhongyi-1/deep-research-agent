import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)


# 加载 .env
load_dotenv()


# =========================
# DeepSeek 配置
# =========================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com",
)

DEEPSEEK_MODEL = os.getenv(
    "DEEPSEEK_MODEL",
    "deepseek-chat",
)


if not DEEPSEEK_API_KEY:
    raise RuntimeError(
        "没有读取到 DEEPSEEK_API_KEY，请检查 .env"
    )


# =========================
# DeepSeek Client
# =========================

deepseek_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)


# =========================
# Agents SDK Model Adapter
# =========================

deepseek_model = OpenAIChatCompletionsModel(
    model=DEEPSEEK_MODEL,
    openai_client=deepseek_client,
)


# 我们没有 OpenAI API Key，
# 所以关闭 OpenAI Tracing 上传
set_tracing_disabled(True)