# 使用指南

本项目提供三种使用入口：CLI、Jupyter Notebook、Gradio Web UI。

!!! warning "必须用 `-m` 方式运行"
    所有入口都要用 `python -m src.xxx` 方式运行。直接 `python src/main.py`
    会把 `src/` 而不是项目根放进 `sys.path`，导致 `ModuleNotFoundError`。

## 1. CLI（快速测试）

```bash
python -m src.main "你的问题"           # LangGraph 标准模式
python -m src.main "你的问题" --deep    # DeepAgents 满配模式
python -m src.main "你的问题" --no-rag  # 跳过检索，纯模型回答
```

不带参数时会使用默认问题。CLI 会先打印当前模型与 LangSmith 追踪状态，
再输出最终答案。

### DeepAgents 满配模式

`--deep` 切换到 DeepAgents：规划 + 子代理 + 虚拟文件系统 + 记忆的满配 Agent。
未安装 `deepagents` 时会打印提示并**自动回退**到 LangGraph 标准模式：

```
⚠️  DeepAgents 模式不可用：DeepAgents 未安装。请 `pip install deepagents`（需 Python 3.11+）
    已自动回退到 LangGraph 标准模式
```

## 2. Jupyter Notebook（交互式学习）

```bash
jupyter notebook notebooks/01_explore.ipynb
```

按顺序执行单元格即可：

- **单元格 1（环境检查）与单元格 3（检索结构）不调用模型**，可以先跑通环境
- 从单元格 2 起会真实调用 LLM，需先配好 Key

适合单步调试：每执行一步都能看到 `ResearchState` 的变化。

## 3. Gradio Web UI（给同事演示）

```bash
python -m src.ui
# 浏览器打开 http://localhost:7860
```

界面左侧输入问题（可勾选 DeepAgents 满配模式），右侧实时显示：

- **执行过程** —— 每个节点的实时日志（计划、检索字符数、反思、写作）
- **最终答案** —— 由 `write` 节点流式输出

直观看到 `plan → retrieve → reflect → write` 的流转。

### 端口占用

```bash
python -m src.ui --server-port 8080   # 换端口
```

## 接自己的数据

RAG 的检索源是 `data/` 目录（可用 `DATA_DIR` 环境变量修改）：

1. 把文档放进 `data/`（支持 `.txt` / `.md` / `.pdf`）
2. 直接运行即可，`retrieve` 节点会自动重建索引
3. 需要调整检索逻辑时改 `src/retriever.py`（如 `top_k`、分块策略）

!!! tip "PDF 支持"
    `.pdf` 解析依赖 PyMuPDF。Docker 镜像已装好 poppler；本地需自行安装依赖。
