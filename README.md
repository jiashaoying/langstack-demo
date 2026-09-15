# LangStack 个人 Demo

一套跑通 **LangChain + LangGraph + DeepAgents + LlamaIndex + LangSmith** 的最小可运行示例。
通过「深度研究助手」这一场景，直观感受各产品的定位与协作方式。

> 一个覆盖 LangChain 全家桶的个人 Demo 项目，从组件调用到复杂 Agent 编排，从本地调试到 Docker 部署、CI 评测，一站式体验 LLM 工程化全链路。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-green.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/jiashaoying/langstack-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/jiashaoying/langstack-demo/actions)

---

## 📌 它是什么

这个项目不是"又一个 Chatbot 模板"，而是一个**教学 + 工程骨架**：

- **LangChain** → 模型 / 工具 / 提示的通用胶水层
- **LlamaIndex** → 数据摄取、索引、RAG 检索
- **LangGraph** → 有状态图编排、循环 / 分支 / 持久化
- **DeepAgents** → 满配自主 Agent（规划 + 子代理 + 文件系统）
- **LangSmith** → 全链路追踪与评测

通过同一个"深度研究助手"场景，展示各框架的**定位差异与协作方式**。

---

## 产品分工

| 产品 | 在本 Demo 中的角色 |
| :--- | :--- |
| **LangChain** | 模型/工具的统一封装、LCEL 管道、提示模板 |
| **LlamaIndex** | 数据/RAG 层：文档加载、索引、检索 |
| **LangGraph** | 有状态工作流：规划→检索→反思→写作 的循环 |
| **DeepAgents** | 满配自主长任务 harness（可选进阶入口） |
| **LangSmith** | 全链路追踪、评测（只需设环境变量） |

## 🏗️ 架构概览

```
用户提问
   │
   ▼
┌─────────────────────────────────────────────┐
│         LangGraph StateGraph                │  ← 编排层
│  plan → retrieve → reflect → write          │
│         ↺ (资料不够则循环检索)               │
├─────────────────────────────────────────────┤
│  retrieve 节点调用 LlamaIndex Retriever     │  ← 数据层
│  (文档 → 索引 → 向量检索 → 返回上下文)      │
├─────────────────────────────────────────────┤
│  LLM 调用通过 LangChain 统一接口             │  ← 模型层
│  (OpenAI / Anthropic / 火山方舟)            │
├─────────────────────────────────────────────┤
│  可选：DeepAgents 满配模式                   │  ← 自主层
│  (规划 + 子代理 + 虚拟文件系统 + 记忆)       │
├─────────────────────────────────────────────┤
│  LangSmith 全链路追踪 & 评测                 │  ← 观测层
└─────────────────────────────────────────────┘
```

---

## 目录结构

```
langstack-demo/
├── .env                    # 密钥配置（不提交）
├── .env.example            # 密钥模板
├── .gitignore
├── LICENSE
├── Dockerfile              # 多阶段构建
├── docker-compose.yml      # 三服务：web / jupyter / verify
├── DOCKER.md               # Docker 部署文档
├── LANGSMITH_EVAL.md       # LangSmith 评测指南
├── requirements.txt        # Python 依赖
├── ruff.toml               # lint 配置
├── data/
│   ├── sample.txt          # 示例文档（RAG 默认检索源）
│   ├── internal_faq.txt    # 私有文档：RAG 评测依赖它
│   └── eval_dataset.jsonl  # LangSmith 评测数据集
├── src/
│   ├── __init__.py
│   ├── config.py           # LangSmith 配置
│   ├── llm.py              # LangChain 模型封装
│   ├── retriever.py        # LlamaIndex 检索器
│   ├── graph.py            # LangGraph 状态图
│   ├── deep_research.py    # DeepAgents 入口
│   ├── main.py             # CLI 入口
│   └── ui.py               # Gradio Web UI
├── notebooks/
│   └── 01_explore.ipynb    # 交互式学习 Notebook
├── scripts/
│   ├── verify.py           # 完整离线验证
│   ├── verify_pure.py      # 零依赖纯逻辑验证
│   ├── evaluate.py         # 离线 / LLM 评测
│   └── ci_local.py         # 本地 CI 模拟
└── .github/
    ├── workflows/ci.yml    # GitHub Actions 流水线
    └── actions/python-setup/ # 复用 action
```

## 快速开始（本地）
### 前置要求

- Python 3.11+
- （可选）Docker & Docker Compose
- （可选）GitHub CLI `gh`

### 1. 克隆 & 安装

```bash
git clone https://github.com/jiashaoying/langstack-demo.git
cd langstack-demo
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置密钥

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

> ⚠️ 方舟和多数平台不同：**拿到 Key 不等于能用模型**，每个模型都要单独开通，
> 否则会收到 `404` 让你误以为模型不存在。这是新手最常踩的坑。
>
> 💰 完成实名后，每个模型送 50 万 tokens（30 天有效），跑通本 Demo 绰绰有余。

要用 OpenAI 官方或 Anthropic Claude，改注释即可，见下方 [模型切换](#模型切换) 一节。

#### Embedding（RAG 检索用，默认已配好）

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

> ⚠️ 方舟的 embedding 模型名都带日期后缀（如 `doubao-embedding-large-text-250515`），
> 且必须先在控制台开通；`doubao-embedding-large` 这类简写并不存在，会报 `404`。

可选：开启 LangSmith 全链路追踪

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
```

### 3. 运行

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

```bash
# 1. 建虚拟环境
python -m venv .venv && source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置密钥（复制后填入真实 key）
cp .env.example .env

# 4. 离线验证（不花钱，确认结构正确）
python scripts/verify.py

# 5. 正式运行
python -m src.main "调研 LangGraph 与 DeepAgents 的取舍"
```

## 三种使用入口

### 🖥️ CLI（快速测试）
```bash
python -m src.main "你的问题"          # LangGraph 模式
python -m src.main "你的问题" --deep  # DeepAgents 模式
```

### 📓 Jupyter Notebook（交互式学习）
```bash
jupyter notebook notebooks/01_explore.ipynb
```
按顺序执行单元格即可。**单元格 1（环境检查）与单元格 3（检索结构）不调用模型；从单元格 2 起会真实调用 LLM，需先配好 Key。**

### 🌐 Gradio Web UI（给同事演示）
```bash
python -m src.ui
# 浏览器打开 http://localhost:7860
```
左侧输入问题，右侧实时显示「执行过程」和「最终答案」，直观看到 plan→retrieve→reflect→write 的流转。

## 🐳 Docker 部署

```bash
# 构建镜像
docker compose build

# 启动 Web UI（默认端口 7860）
docker compose up web

# 启动 Jupyter（默认端口 8888）
docker compose up jupyter

# 运行验证（一次性容器）
docker compose run --rm verify
```

> 源码目录通过 volume 挂载进容器，本地改代码无需重建镜像。

详细文档见 [DOCKER.md](./DOCKER.md)。

---

## 🧪 测试与评测

### 本地验证

```bash
# 零依赖快速校验（CI 最低保障）
python scripts/verify_pure.py

# 完整验证（mock LLM + 检索器）
python scripts/verify.py

# 本地一键模拟 CI 流水线
python scripts/ci_local.py
```

### LangSmith 评测

```bash
# 离线关键词评分
python scripts/evaluate.py

# LLM-as-judge 语义评分（需 API Key）
USE_LLM_JUDGE=true python scripts/evaluate.py
```

| 层级 | 脚本 | 消耗 | 用途 |
| :--- | :--- | :--- | :--- |
| 离线回归 | `evaluate.py` | 无 API 费用（首次需下载约 90MB 本地模型） | CI 门禁、快速验证 |
| LLM-judge | `USE_LLM_JUDGE=true evaluate.py` | API | 语义打分 |
| 在线实验 | LangSmith Datasets | 账号 | 回归对比、生产监控 |

其中有一条 `requires_rag` 用例：答案只存在于 `data/internal_faq.txt`（一份虚构的内部运维
手册，含「夜莺」「蓝鲸」「ZQX-8842」这类不可能出现在公开语料中的标识）。**只有检索真的命中
该文档才可能答对**，所以 RAG 一旦失效，评测会直接判失败 —— 而不是像其余用例那样「靠模型
自身知识也能答对、分数照旧满分」。

详细配置见 [LANGSMITH_EVAL.md](./LANGSMITH_EVAL.md)。

### CI/CD

Push 到 `main` 或开 PR 自动触发 GitHub Actions：

```
lint ──────────┐
verify-pure ───┼──→ gate（全部 success 才放行）
verify-full ───┤
docker ────────┘
```

- `evaluate.py` 在 `verify-full` 内作为一个步骤运行，**不是独立 job**
- 除 `docker` 依赖 `verify-pure`、`gate` 依赖全部外，各 job 之间并行执行
- `verify-full` 会把 embedding 模型缓存到 `.cache/fastembed`（已 gitignore），命中缓存后不再重复下载约 90MB 的模型

所有门禁通过才允许合并。

## 📚 学习路径

1. 先看 `src/llm.py` —— 理解 LangChain 的模型抽象
2. 再看 `src/retriever.py` —— 理解 LlamaIndex 的数据层
3. 然后 `src/graph.py` —— 理解 LangGraph 的状态图编排与循环分支
4. 最后 `src/deep_research.py` —— 理解 DeepAgents 的满配能力
5. 用 Notebook `01_explore.ipynb` 单步执行，实时看状态变化
6. 设好 `LANGSMITH_TRACING=true` 后在 LangSmith 后台看完整 trace 树
7. 接自己的数据：把文档放进 `data/`，必要时改 `src/retriever.py`
8. 演示给非技术同事：`python -m src.ui`

## 说明

- 本 Demo 优先保证**结构清晰、可读、可扩展**，而非功能完备
- 所有 LLM 调用均接入 LangSmith（开启后），可在后台看到每一步的输入/输出/耗时
- DeepAgents **默认未安装**（`requirements.txt` 中已注释，依赖较重）。未装时 `--deep` 会打印提示并自动回退到 LangGraph 标准模式，不会报错中断
- `retriever.py` 对 llama_index 采用**惰性导入**：仅在真正构建索引时才 import，
  因此 `scripts/verify.py` 这类离线验证无需安装 llama_index 即可运行

## 故障排查

| 现象 | 解决 |
| :--- | :--- |
| `python-dotenv` 未安装 | `pip install python-dotenv` |
| DeepAgents 报 ImportError | `pip install deepagents`（需 Python 3.11+）。**它默认未安装**，`requirements.txt` 里是注释掉的 |
| LlamaIndex 报 ImportError | `pip install llama-index`（`verify.py` 无需此步） |
| API 报 401 | 检查 `.env` 中 API Key 是否正确 |
| 首次运行卡在「下载模型」 | 正常：本地 embedding 约 90MB，仅首次。也可改 `EMBEDDING_PROVIDER=openai` 走接口 |
| 检索不到 `data/` 里的文档 | 确认文件确实在 `DATA_DIR`（默认 `./data`）下，且 embedding 能正常出向量 |
| 方舟 `401 AuthenticationError` | Key 无效或过期 → 方舟控制台 → API Key 管理重新生成 |
| 方舟 `403 AccessDenied` | 模型没开通 → 控制台 → 开通管理 → 激活该模型 |
| 方舟 `404 InvalidEndpointOrModel` | `LLM_MODEL` 与控制台显示的模型 ID 不一致，核对后重填 |
| 方舟 embedding 报 `404` | embedding 模型名须带日期后缀（如 `doubao-embedding-large-text-250515`）且已开通 |
| 方舟 `403 AccountOverdueError` | 火山账户余额不足 → 费用中心充值 |
| Gradio 端口占用 | `python -m src.ui --server-port 8080` |

---

## 🔑 模型切换

切换供应商只需改 `.env`（`get_llm()` 会从 `src/config.py` 读取配置）：

```env
LLM_PROVIDER=openai          # openai / anthropic
LLM_MODEL=gpt-4o-mini
```

```python
from src.llm import get_llm

llm = get_llm()                      # 读取 .env 的 LLM_PROVIDER / LLM_MODEL
llm = get_llm(temperature=0.2)
```

业务代码无需改动，改配置即切换供应商（新增供应商只需在 `src/llm.py` 里加一个分支）。

### 接 OpenAI 兼容平台（方舟 / DeepSeek / 通义 / 本地 vLLM）

凡是提供 OpenAI 兼容接口的服务，都**不需要改代码**：保持 `LLM_PROVIDER=openai`，
再加一行 `OPENAI_BASE_URL` 指向该平台即可。`get_llm()` 内部用的是 `ChatOpenAI`，
请求会发到你指定的地址。

```env
LLM_PROVIDER=openai
LLM_MODEL=deepseek-v4-flash-ga-260731
OPENAI_API_KEY=<平台给你的 Key>
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

| 平台 | `OPENAI_BASE_URL` |
| :--- | :--- |
| 火山方舟 | `https://ark.cn-beijing.volces.com/api/v3` |
| OpenAI 官方 | 不设置该行（留空反而会报错） |
| 本地 Ollama / vLLM | `http://localhost:11434/v1` |

> 只有**不兼容 OpenAI 协议**的厂商（如 Anthropic）才需要在 `src/llm.py` 里新增分支。

⚠️ **切换时记得同时改 `LLM_MODEL`**：它是具体模型名，OpenAI 的 `gpt-4o-mini`
不能用在 `anthropic` 上，反之亦然。`src/llm.py` 当前实现了 `openai` 和 `anthropic` 两个分支。

---

## ⚠️ 安全提醒

- **永远不要提交 `.env`**（已在 `.gitignore` 中排除）
- 若曾误提交：`git rm --cached .env` 并从 git 历史清除
- API Key 建议通过环境变量或密钥管理服务注入，不要硬编码

---

## 🤝 技术栈

| 组件 | 角色 | 链接 |
| :--- | :--- | :--- |
| **LangChain** | 通用 LLM 应用框架 | [github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain) |
| **LlamaIndex** | 数据框架 / RAG | [github.com/run-llama/llama_index](https://github.com/run-llama/llama_index) |
| **LangGraph** | 有状态 Agent 编排 | [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) |
| **DeepAgents** | 满配自主 Agent harness | [github.com/langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) |
| **LangSmith** | 观测 / 评测 / 部署 | [smith.langchain.com](https://smith.langchain.com/) |
| **FastEmbed** | 本地 embedding（默认，零成本） | [github.com/qdrant/fastembed](https://github.com/qdrant/fastembed) |
| **Gradio** | Web UI | [gradio.app](https://gradio.app/) |
| **Docker** | 容器化 | [docker.com](https://www.docker.com/) |

---

## 📄 License

MIT