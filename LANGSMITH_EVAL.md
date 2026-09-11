# LangSmith 评测指南

本项目提供三层评测，由轻到重，按需使用：

| 层级 | 脚本 | 依赖 | 用途 |
| :--- | :--- | :--- | :--- |
| 离线回归 | `scripts/evaluate.py` | 无（mock） | CI 门禁、本地快速验证 |
| LLM-as-judge | `USE_LLM_JUDGE=true python scripts/evaluate.py` | 真实 API | 按 rubric 语义打分 |
| 在线评测 | LangSmith Datasets + Experiments | LangSmith 账号 | 数据集版本、回归对比、生产监控 |

## 1. 离线评测（CI 默认）

```bash
python scripts/evaluate.py
```

- 用 `DATASET` 里的关键词做命中率打分
- 通过率 ≥ 75% 才算通过（`sys.exit` 码可用于 CI）
- **不消耗任何 API**，可在无网/无 Key 环境跑

## 2. LLM-as-judge

```bash
cp .env.example .env  # 填 API Key
export USE_LLM_JUDGE=true
python scripts/evaluate.py
```

裁判模型按 `rubric` 给 0-1 分，≥ 0.7 视为通过。适合答案无法用关键词硬匹配的语义评测。

## 3. 数据集文件

`data/eval_dataset.jsonl`：每行一个 JSON，符合 LangSmith Dataset 导入格式。

```json
{
  "inputs": {"query": "..."},
  "outputs": {"expected_keywords": ["..."], "rubric": "..."}
}
```

可在 LangSmith Web → Datasets 直接上传，或用 SDK 导入（见下）。

## 4. LangSmith 在线评测（可选）

### 4.1 上传数据集

```python
from langsmith import Client
client = Client()

dataset = client.create_dataset(
    dataset_name="langstack-research-v1",
    description="深度研究助手评测集",
)
client.create_examples(
    dataset_id=dataset.id,
    examples=[
        {"inputs": {"query": "LangGraph 和 DeepAgents 怎么选？"},
         "outputs": {"expected_keywords": ["LangGraph", "DeepAgents"]}},
        # ... 更多用例
    ],
)
```

### 4.2 定义 evaluator（关键词 / LLM judge）

```python
from langsmith.evaluation import evaluate, EvaluatorType

def keyword_evaluator(run, example) -> dict:
    answer = run.outputs["answer"]
    expected = example.outputs["expected_keywords"]
    hits = sum(1 for kw in expected if kw.lower() in answer.lower())
    return {"key": "keyword_recall", "score": hits / len(expected)}

# 在线实验
evaluate(
    lambda inputs: {"answer": run_research(inputs["query"])},  # 被测目标
    data="langstack-research-v1",                              # 数据集名
    evaluators=[keyword_evaluator, EvaluatorType.LLM_JUDGE],   # 内置 + 自定义
    experiment_prefix="graph-v1",
    metadata={"model": "gpt-4o-mini"},
)
```

### 4.3 接入现有脚本

`scripts/evaluate.py` 的 `DATASET` 与 `keyword_scorer` 可直接复用为 LangSmith evaluator，
无需重写逻辑——本地跑得通的评分器，在线也能用。

## 5. 环境变量

```bash
# .env
LANGSMITH_API_KEY=ls__xxx
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langstack-demo
# 可选：在线评测时指定数据集
LANGSMITH_DATASET=langstack-research-v1
```

开启 `LANGSMITH_TRACING=true` 后，所有 `evaluate.py` 调用都会自动上报，
可在 LangSmith 后台对比不同实验（`experiment_prefix`）的得分曲线。

## 6. 推荐工作流

```
开发 → 本地离线评测 (evaluate.py) → CI 门禁 → 合并
   ↓
生产前 → 上传 Dataset → 在线 LLM-judge 回归 → 对比基线
   ↓
上线后 → 用真实 trace 建新 Dataset → 持续优化
```

## 7. CI 集成

`evaluate.py` 的退出码设计用于 CI：平均分不达标即 `exit(1)`。
可加进 `.github/workflows/ci.yml` 的 `verify-full` 阶段：

```yaml
- name: Run evaluation
  run: python scripts/evaluate.py
  env:
    USE_REAL_API: ${{ secrets.USE_REAL_API }}  # 可选真实评测
```
