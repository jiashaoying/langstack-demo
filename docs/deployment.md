# Docker 部署

一套 Docker 化方案，覆盖「Web UI / Jupyter / 离线验证」三种使用方式。

## 前置

- Docker 20.10+（需支持 BuildKit，Compose v2）
- `docker compose` 子命令可用（Docker Desktop 自带，Linux 需装 `docker-compose-plugin`）
- 一份 `.env` 文件（复制 `.env.example` 后填入真实 API Key）

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY / ANTHROPIC_API_KEY 等
```

## 快速开始

```bash
# 构建镜像（首次或改了依赖后）
docker compose build

# 启动 Web UI（默认服务）
docker compose up web
# 浏览器打开 http://localhost:7860
```

## 三种服务

### 1. Web UI (Gradio) —— 演示给同事/老板

```bash
docker compose up web
```

- 端口：`7860`
- 挂载：`./data → /app/data`（放文档即可被检索）、`./src → /app/src`（热改代码）
- 访问：http://localhost:7860

### 2. Jupyter Notebook —— 交互式学习

```bash
docker compose up jupyter
```

- 端口：`8888`
- 无 token（本地开发用，勿暴露公网）
- 访问：http://localhost:8888
- 打开 `notebooks/01_explore.ipynb` 逐步执行

### 3. 离线验证 —— CI / 本地健康检查

```bash
docker compose run --rm verify
```

- 跑 `scripts/verify.py`，验证图结构、状态流转、循环分支
- `--rm`：运行完自动删除容器
- **不消耗真实 API**，可放心跑

## 常用命令速查

```bash
# 构建（改了 requirements.txt 后必须重新构建）
docker compose build

# 后台启动 Web
docker compose up -d web

# 查看日志
docker compose logs -f web

# 停止
docker compose down

# 进入运行中的容器调试
docker compose exec web bash

# 跑一次 CLI（临时覆盖 command）
docker compose run --rm web python -m src.main "你的问题"

# 清理：停止 + 删除镜像 + 清理 dangling
docker compose down --rmi local
docker image prune -f
```

## 生产/公网部署注意事项

!!! warning "当前配置为本地开发优化"
    Jupyter 无密码、走 HTTP。若部署到公网：

1. **Jupyter**：加 token/password，或用反向代理 + HTTPS（Caddy/Nginx）
2. **Gradio**：用 `share=True`（Gradio 临时公网隧道）或放 Nginx 后
3. **API Key**：用 Docker Secret 或 `.env` 文件权限 `chmod 600`，勿提交 Git
4. **模型/数据**：敏感数据挂载卷加密；考虑用 LangSmith 托管部署
5. **资源限制**：LLM 调用本身轻量，但若启用 DeepAgents 代码执行/沙箱，需限制 CPU/内存：

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## 架构说明

``` mermaid
flowchart TB
    subgraph Host["Docker Host"]
        W["web:7860<br/>Gradio UI"]
        J["jupyter:8888<br/>Notebook"]
        V["verify (run)<br/>一次性验证"]
    end
    W --> IMG
    J --> IMG
    V --> IMG
    IMG["langstack:latest<br/>python:3.11-slim<br/>LangChain + LlamaIndex + LangGraph + Agents"]
    IMG --> VOL["(./data 卷)<br/>文档 / Persist"]
    IMG --> ENV["(.env env_file)<br/>API Keys / 配置"]
```

## 一键健康检查（CI 友好）

```bash
# 完整链路：构建 → 验证 → 启动 → 探活 → 清理
docker compose build && \
docker compose run --rm verify && \
docker compose up -d web && \
sleep 10 && \
curl -sf http://localhost:7860 > /dev/null && echo "✅ Web UI 健康" || echo "❌ Web UI 异常"
docker compose down
```

`verify` 服务使用 `scripts/verify.py`：在完整依赖环境（Docker 镜像内）跑
langgraph 图编译 + mock 全流程；若检测到依赖缺失会自动降级为
`verify_pure.py` 的纯逻辑校验，保证 CI 一定能给出明确结果。
