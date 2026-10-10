# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
@File    : checkpoint.py
@Author  : 你的名字
@Time    : 2026/10/9 20:13
@Desc    : 
"""

import hashlib
import json
import os

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.models import (
    ResearchPlan,
    ResearchEvidence,
)


# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 本地检查点目录
CHECKPOINT_DIR = BASE_DIR / "checkpoints"


def now_iso() -> str:
    """获取当前 UTC 时间。"""
    return datetime.now(timezone.utc).isoformat()


def generate_run_id(query: str) -> str:
    """
    根据用户研究问题生成稳定的任务 ID。

    相同 query 生成相同 ID，
    便于重新运行后找到原来的检查点。
    """
    return hashlib.sha256(
        query.strip().encode("utf-8")
    ).hexdigest()[:16]


class CheckpointState(BaseModel):
    """
    一次 Deep Research 任务的持久化状态。
    """

    version: int = 1

    run_id: str
    query: str

    # 最近完成的执行阶段
    stage: Literal[
        "created",
        "planned",
        "researched",
        "deduplicated",
        "verified",
        "approved",
        "rejected",
        "paused",
        "completed",
    ] = "created"

    # Planner 输出
    plan: ResearchPlan | None = None

    # Research 阶段输出
    evidence_list: list[ResearchEvidence] | None = None

    # 去重后的来源目录
    source_catalog: list[dict] | None = None

    # Verifier 输出
    verification_report: str | None = None

    # 人工审批状态
    review_status: Literal[
        "pending",
        "approved",
        "rejected",
    ] = "pending"

    review_note: str = ""

    # Writer 最终报告
    final_report: str | None = None

    updated_at: str = Field(
        default_factory=now_iso
    )


def checkpoint_path(query: str) -> Path:
    """
    获取本次研究任务对应的检查点文件。
    """
    run_id = generate_run_id(query)

    return CHECKPOINT_DIR / f"{run_id}.json"


def save_checkpoint(
    state: CheckpointState,
) -> Path:
    """
    保存检查点。

    先写入临时文件，再替换正式文件，
    降低写入中断导致文件不完整的风险。
    """

    CHECKPOINT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    state.updated_at = now_iso()

    path = checkpoint_path(state.query)

    # Pydantic 对象转换成可保存的 JSON 数据
    data = state.model_dump(
        mode="json"
    )

    temp_path = path.with_suffix(".json.tmp")

    # 写入临时文件
    with open(
        temp_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

        f.flush()
        os.fsync(f.fileno())

    # 用完整临时文件替换原文件
    os.replace(temp_path, path)

    print(
        f"[Checkpoint] 已保存：{state.stage}"
    )

    print(
        f"[Checkpoint] 文件：{path}"
    )

    return path


def load_or_create_checkpoint(
    query: str,
) -> CheckpointState:
    """
    有检查点就恢复，没有就创建新任务。
    """

    query = query.strip()
    path = checkpoint_path(query)

    if not path.exists():

        state = CheckpointState(
            run_id=generate_run_id(query),
            query=query,
        )

        print(
            "[Checkpoint] 未发现历史任务，准备开始新研究"
        )

        save_checkpoint(state)

        return state

    try:
        raw = path.read_text(
            encoding="utf-8"
        )

        state = CheckpointState.model_validate_json(
            raw
        )

    except Exception as e:
        raise RuntimeError(
            f"检查点读取或校验失败：{path}\n"
            f"具体错误：{e}\n"
            "请检查文件，不要直接覆盖原有数据。"
        ) from e

    if state.version != 1:
        raise RuntimeError(
            f"不支持的检查点版本：{state.version}"
        )

    if state.query != query:
        raise RuntimeError(
            "检查点对应的研究问题不一致"
        )

    print(
        f"[Checkpoint] 发现历史任务：{state.run_id}"
    )

    print(
        f"[Checkpoint] 上次阶段：{state.stage}"
    )

    return state


def reset_checkpoint(
    query: str,
) -> None:
    """
    删除指定问题的历史检查点，
    下次将从 Planner 重新研究。
    """

    path = checkpoint_path(query)

    if path.exists():
        path.unlink()

        print(
            f"[Checkpoint] 已重置：{path.name}"
        )
