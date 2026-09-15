"""
llm.py —— LangChain 模型抽象层

定位：演示 LangChain 的核心价值 —— 用统一接口切换不同模型。
业务代码只依赖 ChatModel 协议，不关心底层是 OpenAI / Anthropic / Google。
"""

from langchain_core.language_models import BaseChatModel

from src.config import settings


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """根据配置返回对应的 ChatModel 实例。

    想换模型？只改 .env 的 LLM_PROVIDER，业务代码零改动。
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.LLM_MODEL, temperature=temperature)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=settings.LLM_MODEL, temperature=temperature)

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


# 系统提示：供各节点复用
RESEARCHER_SYSTEM_PROMPT = """你是一个严谨的研究助手。
规则：
1. 优先依据「检索到的资料」作答，资料不足时明确说明；
2. 给出结论时标注来源编号 [1][2]；
3. 先列要点，再展开细节。
"""
