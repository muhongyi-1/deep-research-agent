# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : test_checkpoint.py
@Author  : 你的名字
@Time    : 2026/10/9 20:35
@Desc    : 
"""

import uuid

from app.checkpoint import (
    load_or_create_checkpoint,
    save_checkpoint,
    reset_checkpoint,
)


def main():

    # 使用唯一测试问题，不影响真实研究
    query = (
        "Day4B Checkpoint Test "
        + uuid.uuid4().hex
    )

    try:

        # 第一次：创建
        state = load_or_create_checkpoint(query)

        assert state.stage == "created"

        print("[PASS] 创建检查点成功")

        # 模拟 Verifier 完成
        state.stage = "verified"
        state.verification_report = (
            "模拟证据核查已经完成"
        )

        save_checkpoint(state)

        # 第二次：恢复
        restored = load_or_create_checkpoint(query)

        assert restored.stage == "verified"

        assert restored.verification_report == (
            "模拟证据核查已经完成"
        )

        print("[PASS] 恢复检查点成功")

        # 测试人工批准状态保存
        restored.review_status = "approved"
        restored.stage = "approved"

        save_checkpoint(restored)

        loaded = load_or_create_checkpoint(query)

        assert loaded.review_status == "approved"

        print("[PASS] 人工审核状态恢复成功")

        print(
            "\n========== Day4-B Checkpoint 测试通过 =========="
        )

    finally:
        # 删除测试生成的检查点
        reset_checkpoint(query)


if __name__ == "__main__":
    main()
