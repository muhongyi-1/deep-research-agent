# Demo 演示指南（Day5-B）

## 目标

用一次可复现的演示，说明：**输入问题 → 规划 → 并发搜索 → 证据核查 → 人工审核 → 引用约束 → 状态恢复 → 离线评测**。

## 演示前检查

1. 项目已激活 `.venv` 且安装依赖。
2. `.env` 包含有效 DeepSeek Key；不要在录屏或截图中展示密钥。
3. `run.py` 是支持 `--fresh`、CLI 输入和 HITL 的 Day4-B 版本。
4. `app/checkpoint.py`、`app/review.py`、`app/citation_guard.py`、`app/evaluation.py` 已放好。
5. 运行规则测试：

```powershell
python test_reliability.py
python test_checkpoint.py
python test_citation_guard.py
python -m unittest test_evaluation.py -v
```

## 演示问题

推荐问题：

```text
比较 LangGraph、OpenAI Agents SDK 和 CrewAI 在工具调用、状态管理与生产级开发中的适用性，给出选型建议并标注来源。
```

### 阶段 1：全新研究

```powershell
python run.py --fresh
```

输入上面同一问题，观察 Planner 的三个任务、Researcher 的搜索日志，以及 Verifier 结果。首次运行会消耗模型 API 额度。

### 阶段 2：人工暂停

在 Human Review 提示处输入 `q`。应看到已暂停、写入 Checkpoint 的提示。

### 阶段 3：断点恢复

```powershell
python run.py
```

再次输入**完全相同**的问题。应看到 Planner、Evidence、来源目录和 Verifier 读取历史记录的提示，然后再次进入人工审核。此轮恢复不应重复调用之前已保存阶段的搜索工具。

### 阶段 4：人工批准并生成报告

输入 `y`。观察 Writer 与 Citation Guard 日志，保存终端中最终的 Markdown 报告（请先脱敏再公开）。

### 阶段 5：离线评测

```powershell
python evaluate_run.py
```

应从最新已完成 Checkpoint 读取数据，输出统计项并在 `eval_reports/` 生成 JSON。评测本身不调用模型，但指标仅是规则层面的代理指标。

## 推荐截图（由你在本地实际运行后截取）

- `01_planner.png`：Planner 生成 3 个研究任务
- `02_parallel_search.png`：Researcher 并发启动，`search_web` 实际返回搜索结果
- `03_verification.png`：Verifier 标记 Supported / Weak / Conflicts
- `04_human_review.png`：人工审核 y/n/q
- `05_checkpoint_resume.png`：重新启动后恢复已有阶段
- `06_citation_guard.png`：合法引用、非法引用和缺失引用审计
- `07_evaluation.png`：运行实际评测结果

可将**脱敏的**截图放在 `docs/screenshots/`。文件存在后，再在 README 中引用图片，避免空链接。

## 90 秒面试讲解稿

> 这是我基于 OpenAI Agents SDK 和 DeepSeek 搭建的 Deep Research Agent。它和普通问答的区别是先规划再执行：Planner 把复杂问题拆成三个研究任务，Researcher 利用 Tool Calling 调用 DDGS 进行真实搜索，并通过 asyncio 并发执行。搜索证据会保留来源信息，统一去重后交给 Verifier 检查摘要证据与结论的一致性。随后进入人工审核，批准后 Writer 才生成报告，并通过 Citation Guard 约束引用编号和 URL。工程层面，我加入了超时、有限重试、退避、并发限制和阶段级 Checkpoint，支持暂停后重新运行恢复；最后使用离线 Evaluation 统计任务、引用和报告结构的规则指标。目前仍是单机原型，下一步重点是全文事实级核验和更完整的评测数据集。

## GitHub 展示注意事项

- 不能公开 `.env`、API Key、含用户数据的 Checkpoint。
- 不要放不存在的测试结果或虚构 QPS、引用准确率、成本收益。
- 如果评测数据不公开，可以展示经过脱敏的统计截图，标注环境、样本数、日期和评测方法。
