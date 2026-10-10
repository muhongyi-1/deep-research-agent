# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : review.py
@Author  : 你的名字
@Time    : 2026/10/9 20:31
@Desc    : 
"""

import asyncio

from app.models import (
    ResearchPlan,
    ResearchEvidence,
)


async def request_human_review(
    plan: ResearchPlan,
    evidence_list: list[ResearchEvidence],
    source_catalog: list[dict],
    verification_report: str,
) -> tuple[str, str]:
    """
    CLI 形式的人工审批。

    返回：
    ("approved", 审批备注)
    ("rejected", 拒绝原因)
    ("paused", 暂停说明)
    """

    print("\n" + "=" * 55)
    print("       Human-in-the-loop 人工审核")
    print("=" * 55)

    # ======================================
    # 1. 显示研究计划
    # ======================================

    print(f"\n研究主题：{plan.topic}")

    print("\n研究任务：")

    for index, task in enumerate(
        plan.tasks,
        start=1,
    ):
        print(
            f"{index}. {task.title}"
        )

    # ======================================
    # 2. 显示研究结果
    # ======================================

    print("\n========== Research Evidence ==========")

    for evidence in evidence_list:

        print(
            f"\n任务：{evidence.task_title}"
        )

        print(
            f"来源数量：{len(evidence.sources)}"
        )

        # 控制终端输出长度
        print(
            evidence.content[:450]
        )

        if len(evidence.content) > 450:
            print("...（证据内容已截断）")

    # ======================================
    # 3. 显示搜索来源
    # ======================================

    print("\n========== Sources ==========")

    for source in source_catalog:

        print(
            f"[{source['id']}] "
            f"{source['title']}"
        )

        print(
            f"URL: {source['url']}"
        )

    # ======================================
    # 4. 显示 Verifier 核查报告
    # ======================================

    print("\n========== Verification Report ==========")

    print(verification_report)

    # ======================================
    # 5. 等待人工操作
    # ======================================

    print("\n请选择下一步操作：")
    print("y = 批准，继续生成最终报告")
    print("n = 拒绝，停止生成报告")
    print("q = 暂停，稍后继续审核")

    while True:

        try:
            # 不直接在异步协程中执行阻塞式 input()
            choice = await asyncio.to_thread(
                input,
                "\n请输入 y / n / q：",
            )

        except EOFError:
            return (
                "paused",
                "当前环境无法进行交互式输入",
            )

        choice = choice.strip().lower()

        if choice == "y":

            print("\n[HITL] 人工审核通过")

            return (
                "approved",
                "人工批准生成最终报告",
            )

        if choice == "n":

            reason = await asyncio.to_thread(
                input,
                "请输入拒绝原因（可留空）：",
            )

            print("\n[HITL] 人工拒绝")

            return (
                "rejected",
                reason.strip() or "人工拒绝",
            )

        if choice == "q":

            print("\n[HITL] 任务已暂停")

            return (
                "paused",
                "等待后续人工审核",
            )

        print(
            "无效选项，请输入 y、n 或 q。"
        )
