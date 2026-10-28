# 架构详解

本项目按「分层架构」组织：每层对应一个 LangChain 家族产品，职责单一、边界清晰。

## 整体架构

``` mermaid
flowchart TB
    subgraph UI["交互层"]
        CLI[CLI<br/>src/main.py]
        WebUI[Web UI<br/>src/ui.py]
        NB[Notebook<br/>01_explore.ipynb]
    end

    subgraph Orche["编排层 · LangGraph"]
        G[src/graph.py<br/>plan → retrieve → reflect → write]
    end

    subgraph Data["数据层 · LlamaIndex"]
        R[src/retriever.py<br/>文档 → 索引 → 向量检索]
    end

    subgraph Model["模型层 · LangChain"]
        L[src/llm.py<br/>OpenAI / Anthropic 统一封装]
    end

    subgraph Auto["自主层 · DeepAgents（可选）"]
        D[src/deep_research.py<br/>规划 + 子代理 + 文件系统]
    end

    CLI --> G
    WebUI --> G
    NB --> G
    G --> R
    G --> L
    R --> L
    D --> R
    D --> L
    L -.-> Obs[LangSmith 观测/评测]
```

## 工作流状态机

`src/graph.py` 用 LangGraph 把深度研究编排成 4 个节点：

``` mermaid
stateDiagram-v2
    [*] --> plan: 用户提问
    plan --> retrieve: 拆出研究计划
    retrieve --> reflect: 检索资料
    reflect --> retrieve: 资料不够（最多 2 轮）
    reflect --> write: 资料足够
    write --> [*]: 最终答案
```

- **plan** —— 把问题拆成 3-5 条研究要点
- **retrieve** —— 调 LlamaIndex 检索器，把私有文档转成上下文
- **reflect** —— 判断资料是否足够，回复 `OK` 或 `MORE: <还需要什么>`
- **write** —— 按 `RESEARCHER_SYSTEM_PROMPT` 综合写出带引用的答案

循环由条件边 `should_continue` 控制：反思结果为 `MORE` 且迭代未超 2 次时回到 `retrieve`。
状态通过 `ResearchState`（TypedDict「黑板」）跨节点共享，`MemorySaver` 提供进程内持久化
（生产可换 `PostgresSaver`）。

## 模块职责

| 文件 | 层 | 职责 |
| :--- | :--- | :--- |
| `src/config.py` | 配置 | 加载 `.env`、暴露 `settings`、初始化 LangSmith 追踪 |
| `src/llm.py` | 模型层 | `get_llm()` 按 provider 返回 ChatModel，业务代码零改动换模型 |
| `src/retriever.py` | 数据层 | 惰性导入 LlamaIndex：建索引 → 取 retriever → 格式化上下文 |
| `src/graph.py` | 编排层 | 组装 StateGraph，定义节点、条件边、checkpointer |
| `src/deep_research.py` | 自主层 | DeepAgents 满配入口，把检索器包装成工具 |
| `src/main.py` | 交互层 | CLI 入口，`--deep` / `--no-rag` 参数 |
| `src/ui.py` | 交互层 | Gradio Web UI，流式展示节点执行过程 |

### 模型层：LangChain

`get_llm()` 只依赖 `ChatModel` 协议，不关心底层是哪家：

```python
from src.llm import get_llm

llm = get_llm()                  # 读 .env 的 LLM_PROVIDER / LLM_MODEL
llm = get_llm(temperature=0.2)
```

切换供应商只改 `.env`，业务代码零改动。新增供应商只需在 `src/llm.py` 加一个分支，
详见 [配置与模型切换](configuration.md)。

### 数据层：LlamaIndex

`retriever.py` 把 `data/` 下的 `.txt/.md/.pdf` 变成可检索的知识：

```python
idx = build_index_from_dir()          # 加载文档 + 构建向量索引
retriever = get_retriever(idx)        # top-4 检索器
context = format_context(retriever, query)  # 带来源编号的上下文字符串
```

产出物是一个 retriever，供 LangGraph 的 `retrieve` 节点调用 —— 这正是
「LlamaIndex 做数据、LangGraph 做编排」的分工体现。

!!! tip "惰性导入"
    `retriever.py` 对 llama_index 采用惰性导入：仅在真正构建索引时才 import。
    因此 `scripts/verify.py` 这类离线验证（mock 掉检索器）无需安装 llama_index
    即可运行。

### 编排层：LangGraph

`build_graph()` 组装出完整状态图。`ResearchState` 是跨节点共享的「黑板」，
`MemorySaver` 提供持久化（断点恢复 / 人机协同）。

```python
from src.graph import run_research

answer = run_research("LangGraph 和 DeepAgents 怎么选？")
```

### 自主层：DeepAgents（可选）

`deep_research.py` 演示几行代码拿到满配 Agent：规划 + 子代理 + 虚拟文件系统 + 记忆。
它把 LlamaIndex 检索器包装成 `search_knowledge_base` 工具，演示产品协作。

!!! note "默认未安装"
    DeepAgents 默认未安装（`requirements.txt` 中已注释，依赖较重）。
    未装时 `--deep` 会打印提示并自动回退到 LangGraph 标准模式，不会报错中断。

## 目录结构

```
langstack-demo/
├── .env.example            # 密钥模板
├── Dockerfile              # 多阶段构建
├── docker-compose.yml      # 三服务：web / jupyter / verify
├── requirements.txt        # Python 依赖
├── data/
│   ├── sample.txt          # 示例文档（RAG 默认检索源）
│   ├── internal_faq.txt    # 私有文档：RAG 评测依赖它
│   └── eval_dataset.jsonl  # LangSmith 评测数据集
├── src/
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
