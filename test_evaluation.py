# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : test_evaluation.py
@Author  : 你的名字
@Time    : 2026/10/9 20:50
@Desc    : 
"""

import unittest

from app.checkpoint import CheckpointState
from app.evaluation import evaluate_checkpoint

from app.models import (
    ResearchPlan,
    ResearchTask,
    ResearchEvidence,
    ResearchSource,
)


class TestEvaluation(unittest.TestCase):

    def create_state(self, report):

        sources = [
            ResearchSource(
                title="Source 1",
                url="https://example.com/a",
                snippet="测试资料1",
            ),
            ResearchSource(
                title="Source 2",
                url="https://example.com/b",
                snippet="测试资料2",
            ),
        ]

        return CheckpointState(
            run_id="evaluation-test",
            query="测试 Agent 评测",
            stage="completed",

            plan=ResearchPlan(
                topic="Agent 评测",
                tasks=[
                    ResearchTask(
                        title="研究任务1",
                        query="Agent evaluation",
                        goal="测试评测指标",
                    )
                ],
            ),

            evidence_list=[
                ResearchEvidence(
                    task_title="研究任务1",
                    query="Agent evaluation",
                    content="测试研究结果",
                    sources=sources,
                )
            ],

            source_catalog=[
                {
                    "id": "S1",
                    "title": "Source 1",
                    "url": "https://example.com/a",
                },
                {
                    "id": "S2",
                    "title": "Source 2",
                    "url": "https://example.com/b",
                },
            ],

            verification_report="核查完成",
            review_status="approved",
            final_report=report,
        )

    def test_citation_metrics(self):

        report = """
# Deep Research Report

## Executive Summary

这是第一条研究结论。[S1]

## Key Findings

这是第二条研究结论。[S99]

## Conclusion

研究结束。

## References

- [S2] Source 2
"""

        state = self.create_state(report)

        result = evaluate_checkpoint(state)

        # 正文有两个引用，其中一个无效
        self.assertEqual(result.total_citations, 2)
        self.assertEqual(result.valid_citations, 1)

        self.assertEqual(
            result.citation_validity_rate,
            0.5,
        )

        # 两个登记来源中只有 S1 被正文引用
        self.assertEqual(
            result.source_utilization_rate,
            0.5,
        )

        self.assertEqual(
            result.invalid_citation_ids,
            ["S99"],
        )

        self.assertEqual(
            result.structure_coverage_rate,
            1.0,
        )

    def test_no_citations(self):

        report = """
# Deep Research Report

## Executive Summary

这是没有任何引用的研究报告。

## Conclusion

研究结束。
"""

        state = self.create_state(report)

        result = evaluate_checkpoint(state)

        self.assertEqual(
            result.total_citations,
            0,
        )

        # 没有引用不能算 100% 合法
        self.assertIsNone(
            result.citation_validity_rate
        )

        self.assertEqual(
            result.cited_sources,
            0,
        )


if __name__ == "__main__":
    unittest.main()
