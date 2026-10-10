# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : evaluate_run.py
@Author  : 你的名字
@Time    : 2026/10/9 20:49
@Desc    : 
"""

import json

from pathlib import Path

from app.checkpoint import (
    CHECKPOINT_DIR,
    CheckpointState,
)

from app.evaluation import evaluate_checkpoint


# 评测结果输出目录
BASE_DIR = Path(__file__).resolve().parent
EVAL_DIR = BASE_DIR / "eval_reports"


def find_latest_completed_checkpoint():
    """
    找到最近一次完成的研究任务。
    """

    if not CHECKPOINT_DIR.exists():
        return None

    files = sorted(
        CHECKPOINT_DIR.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for path in files:

        try:
            state = CheckpointState.model_validate_json(
                path.read_text(encoding="utf-8")
            )

        except Exception as e:
            print(
                f"[Evaluation] 跳过损坏的检查点："
                f"{path.name}，原因：{e}"
            )
            continue

        if (
            state.stage == "completed"
            and state.final_report
        ):
            return state

    return None


def format_percent(value):
    """
    None 表示没有足够数据计算比例。
    """

    if value is None:
        return "N/A"

    return f"{value:.2%}"


def main():

    print("\n========== Deep Research Evaluation ==========\n")

    # ======================================
    # Step 1：加载历史任务
    # ======================================

    state = find_latest_completed_checkpoint()

    if state is None:
        print(
            "没有找到已完成的研究任务。\n"
            "请先运行 python run.py，"
            "人工批准并生成最终报告。"
        )
        return

    print(f"Run ID：{state.run_id}")
    print(f"研究问题：{state.query}")
    print(f"任务状态：{state.stage}")

    # ======================================
    # Step 2：执行离线评测
    # ======================================

    result = evaluate_checkpoint(state)

    # ======================================
    # Step 3：显示评测结果
    # ======================================

    print("\n========== Evaluation Results ==========\n")

    print(
        "研究任务完成率：",
        format_percent(result.research_success_rate),
    )

    print(
        "引用合法率：",
        format_percent(result.citation_validity_rate),
    )

    print(
        "来源利用率：",
        format_percent(result.source_utilization_rate),
    )

    print(
        "报告结构覆盖率：",
        format_percent(result.structure_coverage_rate),
    )

    print(
        "疑似缺少引用的段落：",
        result.uncited_paragraph_count,
    )

    print(
        "引用总次数：",
        result.total_citations,
    )

    print(
        "有效引用次数：",
        result.valid_citations,
    )

    print(
        "未登记引用编号：",
        result.invalid_citation_ids,
    )

    print(
        "Verifier 是否执行：",
        result.verification_present,
    )

    print(
        "人工审批是否通过：",
        result.human_approved,
    )

    # ======================================
    # Step 4：保存评测结果
    # ======================================

    EVAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        EVAL_DIR / f"{state.run_id}_evaluation.json"
    )

    output_path.write_text(
        json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"\n[Evaluation] 结果已保存：{output_path}"
    )


if __name__ == "__main__":
    main()
