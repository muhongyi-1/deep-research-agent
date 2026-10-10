
from urllib.parse import (
    urlsplit,
    urlunsplit,
    parse_qsl,
    urlencode,
)

from app.models import ResearchEvidence


def normalize_url(url: str) -> str:
    """
    规范化 URL，用于判断重复来源。
    不修改原始来源 URL。
    """

    try:
        parts = urlsplit(url.strip())

        if parts.scheme.lower() not in ("http", "https"):
            return ""

        if not parts.netloc:
            return ""

        # 去除常见跟踪参数
        params = [
            (key, value)
            for key, value in parse_qsl(
                parts.query,
                keep_blank_values=True
            )
            if not key.lower().startswith("utm_")
            and key.lower() not in (
                "fbclid",
                "gclid",
            )
        ]

        path = parts.path.rstrip("/") or "/"

        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            urlencode(params),
            "",
        ))

    except ValueError:
        return ""


def build_source_catalog(
    evidence_list: list[ResearchEvidence],
) -> list[dict]:
    """
    将所有 Researcher 的来源统一去重。

    最终生成：
    S1、S2、S3 等全局唯一的来源编号。
    """

    catalog = []
    seen = {}

    for evidence in evidence_list:

        for source in evidence.sources:

            normalized = normalize_url(source.url)

            if not normalized:
                continue

            # 如果来源已经存在，合并任务信息
            if normalized in seen:

                item = seen[normalized]

                if evidence.task_title not in item["tasks"]:
                    item["tasks"].append(
                        evidence.task_title
                    )

                continue

            source_id = f"S{len(catalog) + 1}"

            item = {
                "id": source_id,
                "title": source.title,
                "url": source.url,
                "snippet": source.snippet[:800],
                "tasks": [evidence.task_title],
            }

            seen[normalized] = item
            catalog.append(item)

    return catalog
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : verification.py
@Author  : 你的名字
@Time    : 2026/10/9 14:03
@Desc    : 
"""
