"""
retriever.py —— LlamaIndex 数据/RAG 层

定位：演示 LlamaIndex 的核心价值 —— 把私有文档变成可检索的知识。
产物是一个 retriever，供 LangGraph 工作流调用。

惰性导入说明：
- 模块顶部的 Document / VectorStoreIndex / LlamaSettings / BaseRetriever
  仅为类型提示占位（允许为 None），**真正 import llama_index 发生在函数内部**。
- 这样设计让 `scripts/verify.py` 这类离线验证（mock 掉检索器）无需安装
  llama_index 即可运行；只有真正调用 build_index_from_dir / get_retriever
  时才会触发真实 import。
"""
from pathlib import Path
from src.config import settings

# 类型提示占位：函数内会惰性导入真实类覆盖这些名字
Document = None  # type: ignore
VectorStoreIndex = None  # type: ignore
LlamaSettings = None  # type: ignore
BaseRetriever = object  # type: ignore


def build_index_from_dir(data_dir: str | None = None):
    """从 data_dir 加载文档并构建向量索引。"""
    # 惰性导入：仅在真正构建索引时才依赖 llama_index
    from llama_index.core import Document, VectorStoreIndex, Settings as LlamaSettings
    from llama_index.embeddings.openai import OpenAIEmbedding

    root = Path(data_dir or settings.DATA_DIR)
    if not root.exists():
        raise FileNotFoundError(f"数据目录不存在: {root}")

    docs: list = []
    for path in root.rglob("*"):
        if path.suffix.lower() in {".txt", ".md"}:
            docs.append(Document(text=path.read_text(encoding="utf-8"), metadata={"source": str(path)}))
        elif path.suffix.lower() == ".pdf":
            from llama_index.readers.file import PyMuPDFReader
            docs.extend(PyMuPDFReader().load_data(path))

    if not docs:
        raise RuntimeError(f"{root} 下没有可加载的 .txt/.md/.pdf 文件")

    LlamaSettings.embed_model = OpenAIEmbedding(model=settings.EMBEDDING_MODEL)
    return VectorStoreIndex.from_documents(docs)


def get_retriever(index, top_k: int = 4):
    """返回 top-k 检索器。"""
    return index.as_retriever(similarity_top_k=top_k)


def format_context(retriever, query: str) -> str:
    """检索并格式化为带来源的上下文字符串。"""
    nodes = retriever.retrieve(query)
    if not nodes:
        return "（未检索到相关资料）"
    parts = []
    for i, n in enumerate(nodes, 1):
        src = n.metadata.get("source", "unknown")
        parts.append(f"[Source {i}] {src}\n{n.get_content()}")
    return "\n\n".join(parts)
