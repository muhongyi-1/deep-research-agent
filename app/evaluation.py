# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : evaluation.py
@Author  : 你的名字
@Time    : 2026/10/9 20:47
@Desc    : 
"""

import re

from dataclasses import dataclass, asdict

from app.checkpoint import CheckpointState


# ==========================================
# 1. 引用匹配规则
# ==========================================

# 匹配 [S1]、[S2]、[S100]
CITATION_PATTERN = re.compile(
    r"\[(S\d+)\]"
)

# 匹配 References 标题
REFERENCE_HEADING = re.compile(
    r"(?im)^\s{0,3}#{1,6}\s*"
    r"(?:References|参考文献|参考资料)"
    r"\s*$"
)


# ==========================================
# 2. 评测结果结构
# ==========================================

@dataclass
class EvaluationResult:

    run_id: str
    stage: str

    planned_tasks: int
    successful_tasks: int

    research_success_rate: float | None

    total_sources: int
    cited_sources: int

    source_utilization_rate: float | None

    total_citations: int
    valid_citations: int

    citation_validity_rate: float | None

    invalid_citation_ids: list[str]

    section_checks: dict[str, bool]
    structure_coverage_rate: float

    uncited_paragraph_count: int

    verification_present: bool
    human_approved: bool

    def to_dict(self) -> dict:
        return asdict(self)


# ==========================================
# 3. 提取报告正文
# ==========================================

def extract_report_body(
    report: str,
) -> str:
    """
    只评测报告正文，不统计 References。

    因为 References 本身也有 [S1]，
    如果混在一起会重复统计引用。
    """

    match = REFERENCE_HEADING.search(report)

    if match:
        return report[:match.start()].strip()

    return report.strip()


# ==========================================
# 4. 章节完整性检查
# ==========================================

def check_report_sections(
    report: str,
) -> dict[str, bool]:

    headings = []

    for line in report.splitlines():

        if re.match(
            r"^\s{0,3}#{1,6}\s+",
            line,
        ):
            headings.append(
                re.sub(
                    r"^\s*#{1,6}\s+",
                    "",
                    line,
                ).strip().lower()
            )

    def contains_any(keywords):
        return any(
            any(word in heading for word in keywords)
            for heading in headings
        )

    return {
        "executive_summary": contains_any(
            ["executive summary", "执行摘要"]
        ),
        "key_findings": contains_any(
            ["key findings", "研究发现", "核心发现"]
        ),
        "conclusion": contains_any(
            ["conclusion", "结论"]
        ),
        "references": contains_any(
            ["references", "参考文献", "参考资料"]
        ),
    }


# ==========================================
# 5. 检测疑似缺少引用的段落
# ==========================================

def count_uncited_paragraphs(
    body: str,
    min_length: int = 100,
) -> int:
    """
    只做规则级检查。

    不意味着所有没有引用的段落都是错误的。
    """

    paragraphs = re.split(
        r"\n\s*\n",
        body,
    )

    count = 0

    for paragraph in paragraphs:

        text = paragraph.strip()

        if not text:
            continue

        # 跳过标题、表格和代码块
        if text.startswith(("#", "|", "```")):
            continue

        if text == "---":
            continue

        # 去除空白后计算长度
        plain = re.sub(
            r"\s+",
            "",
            text,
        )

        if len(plain) < min_length:
            continue

        # 已有引用的段落跳过
        if CITATION_PATTERN.search(text):
            continue

        count += 1

    return count


# ==========================================
# 6. Evaluation 主函数
# ==========================================

def evaluate_checkpoint(
    state: CheckpointState,
) -> EvaluationResult:
    """
    对已经保存的研究任务进行离线评测。

    不调用 LLM。
    不调用搜索工具。
    """

    report = state.final_report or ""

    body = extract_report_body(report)

    # --------------------------------------
    # 研究任务完成情况
    # --------------------------------------

    planned_tasks = (
        len(state.plan.tasks)
        if state.plan is not None
        else 0
    )

    evidence_list = state.evidence_list or []

    # 当前用“存在搜索来源”作为完成代理指标
    successful_tasks = sum(
        1 for item in evidence_list
        if len(item.sources) > 0
    )

    research_success_rate = (
        successful_tasks / planned_tasks
        if planned_tasks > 0
        else None
    )

    # --------------------------------------
    # 来源目录
    # --------------------------------------

    source_catalog = (
        state.source_catalog or []
    )

    valid_source_ids = {
        str(item["id"])
        for item in source_catalog
        if isinstance(item, dict)
        and re.fullmatch(
            r"S[1-9]\d*",
            str(item.get("id", ""))
        )
        and str(item.get("url", "")).startswith(
            ("http://", "https://")
        )
    }

    total_sources = len(valid_source_ids)

    # --------------------------------------
    # 引用编号评测
    # --------------------------------------

    citations = CITATION_PATTERN.findall(
        body
    )

    valid_citations = [
        cid for cid in citations
        if cid in valid_source_ids
    ]

    invalid_citation_ids = sorted(
        {
            cid for cid in citations
            if cid not in valid_source_ids
        },
        key=lambda cid: int(cid[1:]),
    )

    total_citations = len(citations)

    # 无引用时用 None，而不是错误地记成 100%
    citation_validity_rate = (
        len(valid_citations) / total_citations
        if total_citations > 0
        else None
    )

    # --------------------------------------
    # 来源利用率
    # --------------------------------------

    unique_cited_sources = set(
        valid_citations
    )

    cited_sources = len(
        unique_cited_sources
    )

    source_utilization_rate = (
        cited_sources / total_sources
        if total_sources > 0
        else None
    )

    # --------------------------------------
    # 报告结构评测
    # --------------------------------------

    section_checks = check_report_sections(
        report
    )

    structure_coverage_rate = (
        sum(section_checks.values())
        / len(section_checks)
    )

    # --------------------------------------
    # 无引用长段落
    # --------------------------------------

    uncited_count = count_uncited_paragraphs(
        body
    )

    # --------------------------------------
    # 返回评测结果
    # --------------------------------------

    return EvaluationResult(
        run_id=state.run_id,
        stage=state.stage,

        planned_tasks=planned_tasks,
        successful_tasks=successful_tasks,

        research_success_rate=research_success_rate,

        total_sources=total_sources,
        cited_sources=cited_sources,

        source_utilization_rate=source_utilization_rate,

        total_citations=total_citations,
        valid_citations=len(valid_citations),

        citation_validity_rate=citation_validity_rate,

        invalid_citation_ids=invalid_citation_ids,

        section_checks=section_checks,
        structure_coverage_rate=structure_coverage_rate,

        uncited_paragraph_count=uncited_count,

        verification_present=bool(
            state.verification_report
            and state.verification_report.strip()
        ),

        human_approved=(
            state.review_status == "approved"
        ),
    )
