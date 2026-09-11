# ============================================================
# 阶段 1: builder —— 安装依赖，预热模型/包
# ============================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 系统依赖（PDF 解析、编译工具等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存层
COPY requirements.txt .
RUN python -m venv .venv && \
    .venv/bin/pip install --no-cache-dir --upgrade pip && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt && \
    # 让 verify 的完整版（依赖 langgraph/langchain_core）能跑通
    .venv/bin/pip install --no-cache-dir langgraph langchain-core

# ============================================================
# 阶段 2: runtime —— 精简运行环境
# ============================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    # 默认配置（可被 docker-compose / .env 覆盖）
    LLM_PROVIDER=openai \
    LLM_MODEL=gpt-4o-mini \
    LANGSMITH_TRACING=false \
    DATA_DIR=/app/data

# 运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PDF 解析依赖
    poppler-utils \
    tesseract-ocr \
    # 常见字体（中文等）
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

WORKDIR /app

# 复制应用代码
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY .env.example .

# 预创建数据目录（挂载卷用）
RUN mkdir -p /app/data

# 非 root 用户运行（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

# 默认启动 Gradio Web UI；可通过 docker-compose command 覆盖为 CLI/verify
CMD ["sh", "-c", "python src/ui.py --server-name 0.0.0.0 --server-port 7860"]
