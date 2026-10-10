
from pydantic import BaseModel, Field


class ResearchTask(BaseModel):
    title: str
    query: str
    goal: str


class ResearchPlan(BaseModel):
    topic: str
    tasks: list[ResearchTask]


class ResearchSource(BaseModel):
    # 搜索结果来源
    title: str
    url: str
    snippet: str = ""


class ResearchEvidence(BaseModel):
    task_title: str
    query: str
    content: str

    # 保留原始来源，不能只存模型总结
    sources: list[ResearchSource] = Field(
        default_factory=list
    )
