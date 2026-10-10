# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : reliability.py
@Author  : 你的名字
@Time    : 2026/10/9 19:53
@Desc    : 
"""

import asyncio
import random

from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    RateLimitError,
)


# 用于表示任意异步函数的返回类型
T = TypeVar("T")


# ==========================================
# 1. 可靠性配置
# ==========================================

@dataclass
class RetryPolicy:
    # 最多尝试次数（包含第一次请求）
    max_attempts: int = 2

    # 每次尝试的超时时间
    timeout_seconds: float = 120.0

    # 初始退避时间
    base_delay_seconds: float = 1.0

    # 最大基础退避时间
    max_delay_seconds: float = 8.0

    # 随机抖动上限
    jitter_seconds: float = 0.5


# ==========================================
# 2. 判断异常是否值得重试
# ==========================================

def is_retryable_error(exc: Exception) -> bool:
    """
    只有临时性故障才自动重试。
    """

    # 超时、网络连接异常
    if isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            OSError,
            APIConnectionError,
            APITimeoutError,
            RateLimitError,
        ),
    ):
        return True

    # HTTP 状态码分类
    if isinstance(exc, APIStatusError):

        status = exc.status_code

        # 请求超时、限流、服务端故障
        return status in (408, 429) or status >= 500

    # 当前 tools.py 会把 DDGS 搜索异常
    # 转换成 JSON error，再由 workflow 抛出 RuntimeError
    if isinstance(exc, RuntimeError):

        message = str(exc).lower()

        # 这里仅兼容当前项目约定的搜索错误
        if "搜索失败" in message:
            return True

    # JSON 解析失败、参数错误等不自动重试
    return False


# ==========================================
# 3. 指数退避计算
# ==========================================

def calculate_backoff(
    attempt: int,
    policy: RetryPolicy,
) -> float:
    """
    attempt 从 1 开始。

    第一次失败：约 1 秒
    第二次失败：约 2 秒
    第三次失败：约 4 秒
    """

    base_delay = min(
        policy.max_delay_seconds,
        policy.base_delay_seconds * (2 ** (attempt - 1)),
    )

    jitter = random.uniform(
        0,
        policy.jitter_seconds,
    )

    return base_delay + jitter


# ==========================================
# 4. 超时 + 重试 + 信号量
# ==========================================

async def run_with_reliability(
    operation: Callable[[], Awaitable[T]],
    task_name: str,
    semaphore: asyncio.Semaphore,
    policy: RetryPolicy,
) -> T:
    """
    对任意异步任务增加：

    1. Semaphore 并发控制
    2. Timeout 超时控制
    3. Retry 自动重试
    4. Exponential Backoff 指数退避

    operation 必须是一个无参数的协程工厂函数。
    """

    if policy.max_attempts < 1:
        raise ValueError(
            "max_attempts 必须大于等于 1"
        )

    if policy.timeout_seconds <= 0:
        raise ValueError(
            "timeout_seconds 必须大于 0"
        )

    for attempt in range(
        1,
        policy.max_attempts + 1,
    ):

        print(
            f"\n[Reliability] {task_name} "
            f"第 {attempt}/{policy.max_attempts} 次尝试"
        )

        try:

            # 限制同一时刻进入研究执行区域的任务数
            async with semaphore:

                # 限制本次操作的等待时间
                result = await asyncio.wait_for(
                    operation(),
                    timeout=policy.timeout_seconds,
                )

            print(
                f"[Reliability] {task_name} 执行成功"
            )

            return result

        except asyncio.CancelledError:
            # 外部取消任务时，不应强行继续重试
            print(
                f"[Reliability] {task_name} 被取消"
            )
            raise

        except Exception as exc:

            print(
                f"[Reliability] {task_name} 执行失败"
            )

            print(
                f"异常类型：{type(exc).__name__}"
            )

            print(
                f"错误信息：{exc}"
            )

            # 判断是否属于可重试故障
            retryable = is_retryable_error(exc)

            # 已达最大次数或不可重试，直接失败
            if (
                not retryable
                or attempt >= policy.max_attempts
            ):

                print(
                    f"[Reliability] {task_name} "
                    "终止重试"
                )

                raise

            # 指数退避
            delay = calculate_backoff(
                attempt,
                policy,
            )

            print(
                f"[Reliability] {task_name} "
                f"等待 {delay:.2f} 秒后重试"
            )

            # 这里必须使用 asyncio.sleep
            # 不能使用 time.sleep 阻塞事件循环
            await asyncio.sleep(delay)

    raise RuntimeError(
        f"任务 {task_name} 重试流程异常结束"
    )
