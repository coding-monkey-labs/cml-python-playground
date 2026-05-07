"""Feature schemas."""

from pydantic import BaseModel


class FeatureCreate(BaseModel):
    name: str
    description: str | None = None
    file_path: str | None = None
    parent_id: int | None = None


class FeatureResponse(BaseModel):
    id: int
    name: str
    description: str | None
    file_path: str | None
    parent_id: int | None
    defect_count: int
    health_score: float

    model_config = {"from_attributes": True}


class FeatureTreeNode(BaseModel):
    name: str
    children: list[str]


class FeatureMetrics(BaseModel):
    feature_name: str
    defect_count: int
    reopen_count: int
    defect_density: float
    health_score: float
