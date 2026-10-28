# 快速开始

从克隆仓库到跑出第一条回答的最短路径。

## 前置要求

- Python 3.11+
- （可选）Docker & Docker Compose
- （可选）GitHub CLI `gh`

## 1. 克隆 & 安装

```bash
git clone https://github.com/jiashaoying/langstack-demo.git
cd langstack-demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 配置密钥

```bash
cp .env.example .env
```

模板默认已配好**火山方舟**（国内可直接访问，新用户有免费额度），你只需替换一个值：

```env
LLM_PROVIDER=openai                                      # 保持不变
LLM_MODEL=deepseek-v4-flash-ga-260731
OPENAI_API_KEY=替换为你的方舟APIKey                      # ← 只改这一行
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

> **为什么 provider 还是 `openai`？**
> 方舟对外提供 OpenAI 兼容接口，所以不用换 SDK，只要把请求地址改成方舟即可，
> `src/llm.py` 一行都不用动。

在正式调用前，还需在 [方舟控制台](https://console.volcengine.com/ark) 完成两步准备：

| 步骤 | 位置 | 不做会怎样 |
| :--- | :--- | :--- |
| 实名认证 | 火山引擎账号中心 | 无法调用任何模型 |
| 开通模型 | 控制台 → 开通管理 | 报 `404 ModelNotOpen` |

!!! warning "方舟和多数平台不同"
    拿到 Key **不等于**能用模型：每个模型都要单独开通，否则会收到 `404`，
    让你误以为模型不存在。这是新手最常踩的坑。

!!! tip "免费额度"
    完成实名后，每个模型送 50 万 tokens（30 天有效），跑通本 Demo 绰绰有余。

要用 OpenAI 官方或 Anthropic Claude，改注释即可，见 [配置与模型切换](configuration.md)。

### Embedding（RAG 检索用，默认已配好）

检索还需要一个 embedding 模型，默认走**本地模型**：不花钱、不需要 Key、离线可用。

```env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

> 首次运行会自动下载约 **90MB** 的模型（缓存在系统临时目录，之后复用）。
> 这一步要联网，但**不消耗任何 API 额度** —— 正因如此，CI 才能跑真实检索。

想改用 OpenAI 兼容服务（方舟 / 通义 / 本地 vLLM / OpenAI 官方）：

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=<对方平台的 embedding 模型名>
```

!!! warning "方舟 embedding 模型名"
    方舟的 embedding 模型名都带日期后缀（如 `doubao-embedding-large-text-250515`），
    且必须先在控制台开通；`doubao-embedding-large` 这类简写并不存在，会报 `404`。

### 可选：开启 LangSmith 全链路追踪

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
```

## 3. 运行

```bash
# 1. 离线验证（不花钱，确认结构正确）
python scripts/verify.py

# 2. 正式运行
python -m src.main "调研 LangGraph 与 DeepAgents 的取舍"
```

| 入口 | 命令 | 用途 |
| :--- | :--- | :--- |
| **CLI** | `python -m src.main "你的问题"` | 快速测试 |
| **CLI (DeepAgents)** | `python -m src.main "问题" --deep` | 满配自主模式（需先 `pip install deepagents`） |
| **CLI（跳过检索）** | `python -m src.main "问题" --no-rag` | 纯模型回答，不查 `data/` |
| **Web UI** | `python -m src.ui` → http://localhost:7860 | 给同事演示 |
| **Notebook** | `jupyter notebook notebooks/01_explore.ipynb` | 单步调试学习 |
| **Docker Web** | `docker compose up web` | 容器化部署 |
| **Docker Jupyter** | `docker compose up jupyter` | 容器化 Notebook |
| **离线验证** | `python scripts/verify_pure.py` | 零依赖，不装任何包也能跑 |

## 下一步

- 想知道每个模块干什么 → [架构详解](architecture.md)
- 想换模型 / 换 embedding → [配置与模型切换](configuration.md)
- 想部署给同事 → [Docker 部署](deployment.md)
- 想按顺序读懂代码 → [学习路径](learning-path.md)
