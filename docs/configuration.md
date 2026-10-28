# 配置与模型切换

所有配置都在 `.env` 中（由 `src/config.py` 加载），业务代码零改动即可切换供应商。

## 环境变量一览

| 变量 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `openai` | 模型供应商：`openai` / `anthropic` |
| `LLM_MODEL` | `gpt-4o-mini` | 具体模型名，换 provider 时必须同步修改 |
| `OPENAI_API_KEY` | — | OpenAI 兼容服务的 Key |
| `OPENAI_BASE_URL` | 空 | OpenAI 兼容服务地址（方舟 / vLLM / Ollama） |
| `ANTHROPIC_API_KEY` | — | Anthropic 的 Key |
| `EMBEDDING_PROVIDER` | `local` | embedding 后端：`local` / `openai` |
| `EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | embedding 模型名 |
| `DATA_DIR` | `./data` | RAG 检索的文档目录 |
| `LANGSMITH_TRACING` | `false` | 是否开启 LangSmith 全链路追踪 |
| `LANGSMITH_API_KEY` | — | LangSmith API Key（`lsv2_...`） |
| `LANGSMITH_PROJECT` | `langstack-demo` | LangSmith 项目名 |

## LLM 模型切换

`get_llm()` 从 `settings` 读 provider 和 model：

```python
from src.llm import get_llm

llm = get_llm()                      # 读取 .env 的 LLM_PROVIDER / LLM_MODEL
llm = get_llm(temperature=0.2)
```

### 方案 A：火山方舟（默认）

方舟提供 OpenAI 兼容接口，`LLM_PROVIDER` 保持 `openai` 不变，
只需把 `OPENAI_BASE_URL` 指向方舟端点：

```env
LLM_PROVIDER=openai
LLM_MODEL=deepseek-v4-flash-ga-260731
OPENAI_API_KEY=<你的方舟 API Key>
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

方舟常用模型（改 `LLM_MODEL` 一行即可切换）：

| 模型 | 特点 |
| :--- | :--- |
| `deepseek-v4-flash-ga-260731` | 响应快，适合本 Demo（默认） |
| `doubao-seed-2-0-mini-260215` | 最便宜 |
| `doubao-seed-2-0-lite-260215` | 性价比均衡 |
| `doubao-seed-2-0-pro-260215` | 质量最好 |

### 方案 B：OpenAI 官方

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-xxx
```

!!! warning "不要设置 `OPENAI_BASE_URL`"
    OpenAI 官方留空即可，设置了反而会报错。

### 方案 C：Anthropic Claude

```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-latest
ANTHROPIC_API_KEY=sk-ant-xxx
```

!!! warning "换 provider 必须同时改 `LLM_MODEL`"
    它是具体模型名：OpenAI 的 `gpt-4o-mini` 不能用在 `anthropic` 上，反之亦然。
    `src/llm.py` 当前实现了 `openai` 和 `anthropic` 两个分支。

## 接任意 OpenAI 兼容平台

凡是提供 OpenAI 兼容接口的服务（方舟 / DeepSeek / 通义 / 本地 vLLM / Ollama），
都**不需要改代码**：保持 `LLM_PROVIDER=openai`，加一行 `OPENAI_BASE_URL` 即可。
`get_llm()` 内部用的是 `ChatOpenAI`，请求会发到你指定的地址。

| 平台 | `OPENAI_BASE_URL` |
| :--- | :--- |
| 火山方舟 | `https://ark.cn-beijing.volces.com/api/v3` |
| OpenAI 官方 | 不设置该行 |
| 本地 Ollama / vLLM | `http://localhost:11434/v1` |

只有**不兼容 OpenAI 协议**的厂商（如 Anthropic）才需要在 `src/llm.py` 里新增分支。

## Embedding 配置

### 本地模型（默认）

```env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

零 API 成本、离线可用。首次运行自动下载约 90MB 模型（缓存在系统临时目录）。

### OpenAI 兼容服务

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=<对方平台的 embedding 模型名>
```

复用上方配好的 `OPENAI_BASE_URL` / `OPENAI_API_KEY`。

!!! warning "方舟 embedding 模型名带日期后缀"
    `doubao-embedding-large-text-250515` 这种才有效；`doubao-embedding-large`
    简写并不存在，会报 `404`。且必须先在控制台开通。

!!! info "实现细节"
    embedding 走的是 `OpenAILikeEmbedding` 而非 `OpenAIEmbedding`：后者会把
    model 强转成 OpenAI 官方模型枚举，第三方模型名会被 `ValueError` 拦下，
    连 HTTP 请求都发不出去。

## LangSmith 追踪（可选）

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=langstack-demo
```

开启后所有 LLM / LangGraph / DeepAgents 调用自动上报 trace，
可在 [smith.langchain.com](https://smith.langchain.com/) 查看每一步的输入/输出/耗时。
