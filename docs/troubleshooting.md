# 故障排查

## 通用问题

| 现象 | 解决 |
| :--- | :--- |
| `python-dotenv` 未安装 | `pip install python-dotenv` |
| DeepAgents 报 ImportError | `pip install deepagents`（需 Python 3.11+）。**它默认未安装**，`requirements.txt` 里是注释掉的 |
| LlamaIndex 报 ImportError | `pip install llama-index`（`verify.py` 无需此步） |
| API 报 401 | 检查 `.env` 中 API Key 是否正确 |
| 首次运行卡在「下载模型」 | 正常：本地 embedding 约 90MB，仅首次。也可改 `EMBEDDING_PROVIDER=openai` 走接口 |
| 检索不到 `data/` 里的文档 | 确认文件确实在 `DATA_DIR`（默认 `./data`）下，且 embedding 能正常出向量 |
| Gradio 端口占用 | `python -m src.ui --server-port 8080` |
| `ModuleNotFoundError: No module named 'src'` | 必须用 `python -m src.main` 方式运行，不要 `python src/main.py` |

## 火山方舟

| 现象 | 原因 | 解决 |
| :--- | :--- | :--- |
| `401 AuthenticationError` | Key 无效或过期 | 方舟控制台 → API Key 管理重新生成 |
| `403 AccessDenied` | 模型没开通 | 控制台 → 开通管理 → 激活该模型 |
| `404 InvalidEndpointOrModel` | `LLM_MODEL` 与控制台显示的模型 ID 不一致 | 核对后重填 |
| embedding 报 `404` | 模型名缺日期后缀 | 用 `doubao-embedding-large-text-250515` 这类完整名称，且先开通 |
| `403 AccountOverdueError` | 火山账户余额不足 | 费用中心充值 |
| 未实名认证 | 任何模型都调不通 | 火山引擎账号中心完成实名 |

## Docker

| 现象 | 可能原因 | 解决 |
| :--- | :--- | :--- |
| `docker compose build` 慢 | 依赖安装/编译 | 首次正常；改依赖后只重建对应层 |
| Web UI 打不开 | 端口占用 | `lsof -i:7860` 换端口 |
| `ModuleNotFoundError` | 代码挂载覆盖了容器包 | 确保 `.venv` 在 `.dockerignore`；重建 `docker compose build` |
| API 报 401 | Key 未注入 | 检查 `.env` 是否在 `env_file` 路径，容器内能读到：`docker compose exec web env \| grep KEY` |
| Jupyter 403 forbidden | token 配置 | 当前已设 `--NotebookApp.token=''`；公网务必加认证 |
| PDF 解析失败 | 缺 poppler | Dockerfile 已装 `poppler-utils`；本地需自行安装 |

## 安全提醒

- **永远不要提交 `.env`**（已在 `.gitignore` 中排除）
- 若曾误提交：`git rm --cached .env` 并从 git 历史清除
- API Key 建议通过环境变量或密钥管理服务注入，不要硬编码
