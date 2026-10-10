# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : test_citation_guard.py
@Author  : 你的名字
@Time    : 2026/10/9 14:48
@Desc    : 
"""

from app.citation_guard import guard_citations


# 模拟真实搜索来源
sources = [
    {
        "id": "S1",
        "title": "LangGraph Documentation",
        "url": "https://docs.langchain.com/",
        "snippet": "LangGraph agent framework",
        "tasks": ["技术框架研究"],
    },
    {
        "id": "S2",
        "title": "OpenAI Agents SDK",
        "url": "https://openai.github.io/openai-agents-python/",
        "snippet": "Agents SDK documentation",
        "tasks": ["技术框架研究"],
    },
]


# 模拟 Writer 的输出
report = """
# Deep Research Report

## 1. Research Findings

LangGraph 是 Agent 开发框架之一。[S1]

OpenAI Agents SDK 支持工具调用。[S2]

某框架市场份额达到 90%。[S99]

查看这个未登记的网站：
https://fake-example.com

## References

- [S99] Fake Reference
"""


result = guard_citations(
    report=report,
    source_catalog=sources,
)

print(result.report)

print("\n========== Citation Audit ==========")
print("合法编号：", result.used_ids)
print("非法编号：", result.invalid_ids)
print("未登记URL：", result.unregistered_urls)

assert result.used_ids == ["S1", "S2"]
assert result.invalid_ids == ["S99"]
assert "https://fake-example.com" not in result.report
assert "【未登记引用：S99】" in result.report

print("\nCitation Guard 测试通过")
