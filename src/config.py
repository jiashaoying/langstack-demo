"""
config.py —— 统一配置中心

负责：加载 .env、暴露全局设置、初始化 LangSmith 追踪。
其它模块都从这里取配置，避免到处读环境变量。
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


# ---- LangSmith 追踪开关 ----
# 设为 true 后，所有 LangChain/LangGraph/DeepAgents 调用自动上报 trace
if _get("LANGSMITH_TRACING", "false").lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = _get("LANGSMITH_PROJECT", "langstack-demo")


class Settings:
    LLM_PROVIDER = _get("LLM_PROVIDER", "openai")
    LLM_MODEL = _get("LLM_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "text-embedding-3-small")
    DATA_DIR = _get("DATA_DIR", "./data")
    LANGSMITH_TRACING = _get("LANGSMITH_TRACING", "false").lower() == "true"


settings = Settings()
