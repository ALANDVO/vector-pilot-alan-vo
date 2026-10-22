from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict
import json


class EvaluationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_name: str = Field(..., min_length=1, max_length=255)
    dataset_version: str = Field(default="1.0", max_length=50)
    config: Optional[dict[str, Any]] = None


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_name: Optional[str] = Field(None, min_length=1, max_length=255)
    dataset_version: Optional[str] = Field(None, max_length=50)
    config: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class EvaluationRead(EvaluationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    config: Optional[str] = None  # Stored as JSON string in DB

    @property
    def config_dict(self) -> Optional[dict[str, Any]]:
        if self.config:
            return json.loads(self.config)
        return None


class EvaluationRunBase(BaseModel):
    model_provider: str = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=255)
    model_config_json: Optional[dict[str, Any]] = None


class EvaluationRunCreate(EvaluationRunBase):
    pass


class EvaluationRunRead(EvaluationRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluation_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @property
    def model_config_dict(self) -> Optional[dict[str, Any]]:
        if self.model_config_json:
            return json.loads(self.model_config_json)
        return None


class EvaluationMetricBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    value: float
    details: Optional[dict[str, Any]] = None


class EvaluationMetricRead(EvaluationMetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int

    @property
    def details_dict(self) -> Optional[dict[str, Any]]:
        if self.details:
            return json.loads(self.details)
        return None


class EvaluationWithRuns(EvaluationRead):
    runs: list[EvaluationRunRead] = []


class EvaluationRunWithMetrics(EvaluationRunRead):
    metrics: list[EvaluationMetricRead] = []


class EvaluationListResponse(BaseModel):
    items: list[EvaluationRead]
    total: int
    page: int
    page_size: int