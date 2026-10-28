# 学习路径

按文件顺序读懂全项目，每个文件都只演示一个核心概念。

## 推荐顺序

1. **`src/llm.py`** —— 理解 LangChain 的模型抽象
   - `get_llm()` 用统一接口切换 OpenAI / Anthropic，业务代码不感知供应商
   - 重点：`BaseChatModel` 协议、惰性导入
2. **`src/retriever.py`** —— 理解 LlamaIndex 的数据层
   - 文档 → 索引 → retriever → 带来源的上下文
   - 重点：惰性导入设计（离线验证不装 llama_index 也能跑）、
     `OpenAILikeEmbedding` vs `OpenAIEmbedding` 的坑
3. **`src/graph.py`** —— 理解 LangGraph 的状态图编排
   - `ResearchState` 黑板、4 个节点、条件边循环、`MemorySaver` checkpointer
   - 重点：`should_continue` 如何控制循环、TypedDict 状态设计
4. **`src/deep_research.py`** —— 理解 DeepAgents 的满配能力
   - 几行代码拿到规划 + 子代理 + 虚拟文件系统 + 记忆
   - 重点：把 LlamaIndex 检索器包装成工具的产品协作
5. **`src/config.py`** —— 配置中心
   - `.env` 加载、`settings` 单例、LangSmith 追踪开关
6. **`src/main.py` / `src/ui.py`** —— 交互层
   - CLI 参数解析、Gradio 流式输出（`stream_mode=["updates", "messages"]`）

## 动手实验

1. 用 Notebook `notebooks/01_explore.ipynb` 单步执行，实时看 `ResearchState` 变化
2. 设好 `LANGSMITH_TRACING=true` 后在 LangSmith 后台看完整 trace 树
3. 接自己的数据：把文档放进 `data/`，必要时改 `src/retriever.py`
4. 演示给非技术同事：`python -m src.ui`
5. 尝试修改：
   - 把循环上限从 2 次改成 3 次（`src/graph.py` 的 `should_continue`）
   - 把 `top_k` 从 4 调到 6（`src/retriever.py` 的 `get_retriever`）
   - 新增一个供应商分支（`src/llm.py` 的 `get_llm`）
   - 换 `MemorySaver` 为 `SqliteSaver` 体验持久化

## 设计说明

- 本 Demo 优先保证**结构清晰、可读、可扩展**，而非功能完备
- 所有 LLM 调用均接入 LangSmith（开启后），可在后台看到每一步的输入/输出/耗时
- DeepAgents **默认未安装**（`requirements.txt` 中已注释，依赖较重）。
  未装时 `--deep` 会打印提示并自动回退到 LangGraph 标准模式，不会报错中断
- `retriever.py` 对 llama_index 采用**惰性导入**：仅在真正构建索引时才 import，
  因此 `scripts/verify.py` 这类离线验证无需安装 llama_index 即可运行
