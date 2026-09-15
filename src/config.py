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
    # local  —— 本地模型（默认）：零 API 成本、离线可用，clone 下来即可跑通 RAG
    # openai —— 任意 OpenAI 兼容服务（方舟 / OpenAI 官方 / 通义 / 本地 vLLM）
    EMBEDDING_PROVIDER = _get("EMBEDDING_PROVIDER", "local")
    # 默认值对应 local 模式下的中文检索模型
    EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    DATA_DIR = _get("DATA_DIR", "./data")
    LANGSMITH_TRACING = _get("LANGSMITH_TRACING", "false").lower() == "true"
    # embedding 同样复用 OpenAI 兼容接口（方舟 / DeepSeek / 通义 / 本地 vLLM）。
    # 这两个值必须显式传给 embedding 实现类，不能指望它自己读到环境变量：
    # OpenAILikeEmbedding 的 api_key 默认值是字符串 'fake'，漏传会直接鉴权失败。
    OPENAI_BASE_URL = _get("OPENAI_BASE_URL", "")
    OPENAI_API_KEY = _get("OPENAI_API_KEY", "")


settings = Settings()
