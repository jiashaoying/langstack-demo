# CI/CD

Push 到 `main` 或开 PR 自动触发 GitHub Actions 流水线（`.github/workflows/ci.yml`）。

## 流水线结构

``` mermaid
flowchart TB
    L[lint<br/>ruff + black]
    VP[verify-pure<br/>零依赖验证]
    VF[verify-full<br/>完整验证 + 评测]
    D[docker<br/>构建镜像 + 容器内验证]
    G{gate<br/>全部 success 才放行}

    L --> G
    VP --> G
    VP --> D
    VF --> G
    D --> G
```

## Job 说明

| Job | 做什么 | 依赖 |
| :--- | :--- | :--- |
| `lint` | Ruff 检查 + Black 格式检查 | — |
| `verify-pure` | 零依赖纯逻辑验证（最低保障） | — |
| `verify-full` | 装全依赖，跑 LangGraph mock 全流程 + 离线评测 | — |
| `docker` | `docker compose build` + 容器内验证 | `verify-pure` |
| `gate` | 汇总门禁，全部 success 才绿 | 所有 job |

- `evaluate.py` 在 `verify-full` 内作为一个步骤运行，**不是独立 job**
- 除 `docker` 依赖 `verify-pure`、`gate` 依赖全部外，各 job 之间并行执行
- 所有门禁通过才允许合并

## 复用 Action

`.github/actions/python-setup/` 是一个本地复用 action，封装了 Python 环境准备，
各 job 通过 `uses: ./.github/actions/python-setup` 引用，避免重复配置。

## 缓存策略

`verify-full` 会把 embedding 模型缓存到 `.cache/fastembed`（已 gitignore）：

- **Key 用 `src/config.py` 的 hash**：默认 `EMBEDDING_MODEL` 定义在其中，
  换模型时它必然变动，缓存随之自动失效，无需手工维护版本号
- `FASTEMBED_CACHE_PATH` 固定到仓库内路径，runner 上才能被 `actions/cache` 命中
- 命中缓存后不再重复下载约 90MB 的模型

## 本地模拟 CI

```bash
python scripts/ci_local.py
```

一键在本地按相同顺序跑完 lint / 验证 / 评测，推送前先自测。

## 文档站部署流水线

`.github/workflows/deploy-pages.yml` 负责把 `docs/` 目录用 MkDocs 构建并部署到
GitHub Pages（本网站），与代码 CI 相互独立：

- 只在 push 到 `main` 或手动触发（`workflow_dispatch`）时运行
- 不影响代码门禁；文档构建失败不会阻塞 PR
