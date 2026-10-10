"""Free web search tool for the Deep Research Agent."""

import asyncio
import json

from agents import function_tool
from ddgs import DDGS


def _search_sync(query: str) -> list[dict]:
    """Run the blocking DDGS request in a worker thread."""
    with DDGS(timeout=15) as client:
        items = client.text(query, max_results=5) or []
    return [
        {
            "title": str(item.get("title") or ""),
            "url": str(item.get("href") or item.get("url") or ""),
            "content": str(item.get("body") or item.get("content") or "")[:1200],
        }
        for item in items
        if isinstance(item, dict)
    ]


@function_tool(strict_mode=False)
async def search_web(query: str) -> str:
    """Search the public web and return result titles, URLs and snippets.

    Args:
        query: Search query to send to the web search provider.
    """
    print(f"\n[search_web] 开始搜索：{query}")
    try:
        results = await asyncio.to_thread(_search_sync, query)
        print(f"[search_web] 搜索完成：{len(results)} 条结果")
        return json.dumps({"query": query, "results": results}, ensure_ascii=False)
    except Exception as exc:
        # Researcher parses this error and Reliability Layer decides whether to retry.
        print(f"[search_web] 搜索失败：{type(exc).__name__}: {exc}")
        return json.dumps(
            {"query": query, "error": f"{type(exc).__name__}: {exc}", "results": []},
            ensure_ascii=False,
        )
