# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : test_reliability.py
@Author  : 你的名字
@Time    : 2026/10/9 19:57
@Desc    : 
"""

import asyncio

from app.reliability import (
    RetryPolicy,
    run_with_reliability,
)


# ==========================================
# 测试 1：第一次失败，第二次成功
# ==========================================

async def test_retry():

    attempts = 0

    async def unstable_task():
        nonlocal attempts

        attempts += 1

        if attempts == 1:
            raise ConnectionError("模拟网络断开")

        return "研究任务成功"

    policy = RetryPolicy(
        max_attempts=2,
        timeout_seconds=2,
        base_delay_seconds=0.01,
        jitter_seconds=0,
    )

    result = await run_with_reliability(
        operation=unstable_task,
        task_name="Retry 测试",
        semaphore=asyncio.Semaphore(2),
        policy=policy,
    )

    assert result == "研究任务成功"
    assert attempts == 2

    print("\n[PASS] Retry 测试通过")


# ==========================================
# 测试 2：任务超时
# ==========================================

async def test_timeout():

    async def slow_task():
        await asyncio.sleep(0.2)
        return "完成"

    policy = RetryPolicy(
        max_attempts=1,
        timeout_seconds=0.02,
    )

    try:
        await run_with_reliability(
            operation=slow_task,
            task_name="Timeout 测试",
            semaphore=asyncio.Semaphore(2),
            policy=policy,
        )

    except TimeoutError:
        print("\n[PASS] Timeout 测试通过")
        return

    raise AssertionError(
        "任务应当发生 TimeoutError"
    )


# ==========================================
# 测试 3：限制并发数量
# ==========================================

async def test_semaphore():

    active = 0
    max_active = 0

    semaphore = asyncio.Semaphore(2)

    policy = RetryPolicy(
        max_attempts=1,
        timeout_seconds=2,
    )

    async def simulated_research():
        nonlocal active, max_active

        active += 1

        max_active = max(
            max_active,
            active,
        )

        try:
            await asyncio.sleep(0.05)
            return "OK"

        finally:
            active -= 1

    tasks = [
        run_with_reliability(
            operation=simulated_research,
            task_name=f"Task-{i}",
            semaphore=semaphore,
            policy=policy,
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    assert all(item == "OK" for item in results)
    assert max_active == 2

    print(
        f"\n[PASS] Semaphore 测试通过，"
        f"最大并发数：{max_active}"
    )


# ==========================================
# 测试 4：不可重试错误
# ==========================================

async def test_non_retryable():

    attempts = 0

    async def invalid_request():
        nonlocal attempts

        attempts += 1
        raise ValueError("模拟参数错误")

    try:
        await run_with_reliability(
            operation=invalid_request,
            task_name="参数错误测试",
            semaphore=asyncio.Semaphore(2),
            policy=RetryPolicy(max_attempts=3),
        )

    except ValueError:
        assert attempts == 1
        print(
            "\n[PASS] 不可重试错误测试通过"
        )
        return

    raise AssertionError("预期出现 ValueError")


async def main():
    await test_retry()
    await test_timeout()
    await test_semaphore()
    await test_non_retryable()

    print("\n========== 所有可靠性测试通过 ==========")


if __name__ == "__main__":
    asyncio.run(main())
