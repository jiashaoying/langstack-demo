---
hide:
  - toc
---

# LangStack 个人 Demo

一套跑通 **LangChain + LangGraph + DeepAgents + LlamaIndex + LangSmith** 的最小可运行示例。

通过「深度研究助手」这一场景，直观感受各产品的定位与协作方式：

- **LangChain** → 模型 / 工具 / 提示的通用胶水层
- **LlamaIndex** → 数据摄取、索引、RAG 检索
- **LangGraph** → 有状态图编排、循环 / 分支 / 持久化
- **DeepAgents** → 满配自主 Agent（规划 + 子代理 + 文件系统）
- **LangSmith** → 全链路追踪与评测

这不是"又一个 Chatbot 模板"，而是一个**教学 + 工程骨架**：从组件调用到复杂 Agent
编排，从本地调试到 Docker 部署、CI 评测，一站式体验 LLM 工程化全链路。

[快速开始](getting-started.md){ .md-button .md-button--primary }
[架构详解](architecture.md){ .md-button }
[:fontawesome-brands-github: 查看源码](https://github.com/jiashaoying/langstack-demo){ .md-button }

---

## 产品分工

| 产品 | 在本 Demo 中的角色 |
| :--- | :--- |
| **LangChain** | 模型/工具的统一封装、LCEL 管道、提示模板 |
| **LlamaIndex** | 数据/RAG 层：文档加载、索引、检索 |
| **LangGraph** | 有状态工作流：规划 → 检索 → 反思 → 写作 的循环 |
| **DeepAgents** | 满配自主长任务 harness（可选进阶入口） |
| **LangSmith** | 全链路追踪、评测（只需设环境变量） |

## 核心工作流

``` mermaid
flowchart LR
    A[用户提问] --> B[plan<br/>拆解研究计划]
    B --> C[retrieve<br/>LlamaIndex 检索]
    C --> D[reflect<br/>反思资料是否足够]
    D -->|资料不足| C
    D -->|足够| E[write<br/>综合写作]
    E --> F[最终答案]
```

## 三种使用入口

| 入口 | 命令 | 适合场景 |
| :--- | :--- | :--- |
| **CLI** | `python -m src.main "你的问题"` | 快速测试 |
| **Web UI** | `python -m src.ui` | 给同事演示 |
| **Notebook** | `jupyter notebook notebooks/01_explore.ipynb` | 交互式学习 |

外加 `--deep` 参数可切换 DeepAgents 满配模式，`--no-rag` 可跳过检索。

## 技术栈

| 组件 | 角色 | 链接 |
| :--- | :--- | :--- |
| **LangChain** | 通用 LLM 应用框架 | [:fontawesome-brands-github:](https://github.com/langchain-ai/langchain) |
| **LlamaIndex** | 数据框架 / RAG | [:fontawesome-brands-github:](https://github.com/run-llama/llama_index) |
| **LangGraph** | 有状态 Agent 编排 | [:fontawesome-brands-github:](https://github.com/langchain-ai/langgraph) |
| **DeepAgents** | 满配自主 Agent harness | [:fontawesome-brands-github:](https://github.com/langchain-ai/deepagents) |
| **LangSmith** | 观测 / 评测 / 部署 | [smith.langchain.com](https://smith.langchain.com/) |
| **FastEmbed** | 本地 embedding（默认，零成本） | [:fontawesome-brands-github:](https://github.com/qdrant/fastembed) |
| **Gradio** | Web UI | [gradio.app](https://gradio.app/) |
| **Docker** | 容器化 | [docker.com](https://www.docker.com/) |

## 文档导航

- [快速开始](getting-started.md) —— 克隆到第一条回答的最短路径
- [架构详解](architecture.md) —— 分层设计与模块职责
- [使用指南](usage.md) —— CLI / Web UI / Notebook 三种入口
- [配置与模型切换](configuration.md) —— 方舟 / OpenAI / Anthropic 与 embedding
- [Docker 部署](deployment.md) —— 容器化运行三种服务
- [测试与评测](evaluation.md) —— 离线验证、LangSmith 评测
- [CI/CD](ci.md) —— GitHub Actions 流水线说明
- [学习路径](learning-path.md) —— 按文件顺序读懂全项目
- [故障排查](troubleshooting.md) —— 常见报错速查
