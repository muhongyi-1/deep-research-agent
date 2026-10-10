# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : citation_guard.py
@Author  : 你的名字
@Time    : 2026/10/9 14:46
@Desc    : 
"""

import re
from dataclasses import dataclass, field

from app.verification import normalize_url


# 匹配单个来源编号：[S1]、[S12]
CITATION_PATTERN = re.compile(
    r"\[(S\d+)\]"
)

# 匹配组合引用：[S1, S2]
COMBINED_PATTERN = re.compile(
    r"\[(S\d+(?:\s*[,，、;；]\s*S\d+)+)\]"
)

# 匹配正文中的 URL
URL_PATTERN = re.compile(
    r"https?://[^\s<>\]\)\"']+"
)

# 匹配 Markdown 链接
MARKDOWN_LINK_PATTERN = re.compile(
    r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)"
)

# 匹配模型自行生成的 References 标题
REFERENCES_PATTERN = re.compile(
    r"(?im)^\s{0,3}#{1,6}\s*"
    r"(?:\d+[.、．]?\s*)?"
    r"(?:references|参考文献|参考资料)"
    r"\s*[:：]?\s*$"
)


@dataclass
class CitationGuardResult:
    """
    Citation Guard 的校验结果。
    """

    report: str

    # 最终报告实际使用的合法引用
    used_ids: list[str] = field(
        default_factory=list
    )

    # 模型生成的非法引用编号
    invalid_ids: list[str] = field(
        default_factory=list
    )

    # 被移除的未登记 URL
    unregistered_urls: list[str] = field(
        default_factory=list
    )

    # 缺少有效引用的较长段落
    uncited_blocks: list[str] = field(
        default_factory=list
    )


def remove_generated_references(
    report: str
) -> str:
    """
    移除模型自己生成的 References。

    最终参考文献由 Python 根据真实来源目录生成，
    不依赖模型自由填写。
    """

    match = REFERENCES_PATTERN.search(report)

    if match:
        return report[:match.start()].rstrip()

    return report.strip()


def normalize_citation_format(
    report: str
) -> str:
    """
    将组合引用统一转换为独立编号。

    例如：
    [S1, S2] -> [S1][S2]
    """

    def replace(match):
        ids = re.split(
            r"\s*[,，、;；]\s*",
            match.group(1),
        )

        return "".join(
            f"[{source_id}]"
            for source_id in ids
        )

    return COMBINED_PATTERN.sub(
        replace,
        report,
    )


def find_uncited_blocks(
    report: str,
    min_length: int = 80,
) -> list[str]:
    """
    查找可能缺少来源的较长段落。

    注意：
    这里只做格式层面的风险检测，
    不能证明段落是否属于事实性陈述。
    """

    blocks = re.split(
        r"\n\s*\n",
        report,
    )

    uncited = []

    for block in blocks:

        text = block.strip()

        if not text:
            continue

        # 跳过纯标题、分隔符和代码块
        if text.startswith("#"):
            continue

        if text.startswith("```"):
            continue

        if text == "---":
            continue

        # 过短的文本暂时不检查
        plain_text = re.sub(
            r"[#*`>|\-\s]",
            "",
            text,
        )

        if len(plain_text) < min_length:
            continue

        # 已包含合法引用的段落跳过
        if CITATION_PATTERN.search(text):
            continue

        uncited.append(
            text[:160]
        )

    return uncited


def guard_citations(
    report: str,
    source_catalog: list[dict],
) -> CitationGuardResult:
    """
    Citation Guard 主函数。

    实现：
    1. 建立可信来源编号白名单
    2. 清除模型生成的 References
    3. 统一引用格式
    4. 标记非法来源编号
    5. 移除未登记 URL
    6. 检测未引用的较长段落
    7. 自动生成真实 References
    """

    # ======================================
    # Step 1：构建合法来源索引
    # ======================================

    source_index = {}
    allowed_urls = set()

    for item in source_catalog:

        source_id = str(
            item.get("id", "")
        )

        url = str(
            item.get("url", "")
        )

        # 校验来源编号
        if not re.fullmatch(
            r"S[1-9]\d*",
            source_id,
        ):
            continue

        # 校验 URL
        normalized = normalize_url(url)

        if not normalized:
            continue

        source_index[source_id] = item
        allowed_urls.add(normalized)

    if not source_index:
        raise ValueError(
            "Citation Guard 没有收到合法来源目录"
        )

    # ======================================
    # Step 2：删除模型自己的 References
    # ======================================

    body = remove_generated_references(
        report
    )

    # ======================================
    # Step 3：统一引用格式
    # ======================================

    body = normalize_citation_format(
        body
    )

    # ======================================
    # Step 4：检查引用编号
    # ======================================

    invalid_ids = set()

    def check_citation(match):

        source_id = match.group(1)

        if source_id in source_index:
            return match.group(0)

        invalid_ids.add(source_id)

        # 不允许未登记引用继续伪装为合法引用
        return f"【未登记引用：{source_id}】"

    body = CITATION_PATTERN.sub(
        check_citation,
        body,
    )

    # ======================================
    # Step 5：拦截未登记 URL
    # ======================================

    unregistered_urls = set()

    def is_allowed(url: str) -> bool:
        normalized = normalize_url(
            url.rstrip(".,;:!?，。；：！？")
        )

        return normalized in allowed_urls

    # 先处理 Markdown 链接，避免破坏链接结构
    def check_markdown_link(match):

        label = match.group(1)
        url = match.group(2)

        if is_allowed(url):
            return match.group(0)

        unregistered_urls.add(url)

        return (
            f"{label}（未登记链接已移除）"
        )

    body = MARKDOWN_LINK_PATTERN.sub(
        check_markdown_link,
        body,
    )

    # 再处理独立出现的原始 URL
    def check_url(match):

        raw_url = match.group(0)

        url = raw_url.rstrip(
            ".,;:!?，。；：！？"
        )

        suffix = raw_url[len(url):]

        if is_allowed(url):
            return raw_url

        unregistered_urls.add(url)

        return "【未登记网址已移除】" + suffix

    body = URL_PATTERN.sub(
        check_url,
        body,
    )

    # ======================================
    # Step 6：统计合法引用
    # ======================================

    used_set = set(
        CITATION_PATTERN.findall(body)
    )

    # 按数字顺序排列：S1、S2、S10
    used_ids = sorted(
        used_set,
        key=lambda x: int(x[1:]),
    )

    # ======================================
    # Step 7：检测可能遗漏的引用
    # ======================================

    uncited_blocks = find_uncited_blocks(
        body
    )

    # ======================================
    # Step 8：生成安全提示
    # ======================================

    warnings = []

    if invalid_ids:
        warnings.append(
            f"发现 {len(invalid_ids)} 个未登记引用，"
            "已在正文中标记。"
        )

    if unregistered_urls:
        warnings.append(
            f"发现 {len(unregistered_urls)} 个"
            "未登记 URL，已从正文中移除。"
        )

    if uncited_blocks:
        warnings.append(
            f"发现 {len(uncited_blocks)} 个"
            "可能缺少引用的较长段落，需复核。"
        )

    if not used_ids:
        warnings.append(
            "正文没有使用任何有效的来源编号。"
        )

    if warnings:

        body += (
            "\n\n> **Citation Guard 提示：** "
            + " ".join(warnings)
        )

    # ======================================
    # Step 9：自动生成 References
    # ======================================

    references = [
        "## References"
    ]

    if used_ids:

        for source_id in used_ids:

            source = source_index[source_id]

            title = str(
                source.get("title", "")
            ).replace("\n", " ").strip()

            url = source["url"]

            references.append(
                f"- [{source_id}] {title}\n"
                f"  {url}"
            )

    else:
        references.append(
            "当前报告未包含有效来源引用。"
        )

    final_report = (
        body
        + "\n\n---\n\n"
        + "\n\n".join(references)
    )

    # ======================================
    # Step 10：返回审计结果
    # ======================================

    return CitationGuardResult(
        report=final_report,
        used_ids=used_ids,
        invalid_ids=sorted(invalid_ids),
        unregistered_urls=sorted(
            unregistered_urls
        ),
        uncited_blocks=uncited_blocks,
    )
