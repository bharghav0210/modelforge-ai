from typing import Literal, Any
from pydantic import BaseModel, Field, ConfigDict

class TrainRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dataset_id: str
    task: Literal['classification', 'regression', 'clustering', 'nlp', 'neural_classification', 'neural_regression']
    algorithm: str
    target: str | None = None
    text_column: str | None = None
    test_size: float = Field(default=0.25, ge=0.15, le=0.4)
    seed: int = Field(default=42, ge=0, le=2147483647)
    clusters: int = Field(default=3, ge=2, le=12)
    hidden_layers: list[int] = Field(default=[32, 16], min_length=1, max_length=3)
    iterations: int = Field(default=150, ge=20, le=500)

class RegisterRequest(BaseModel):
    experiment_id: str
    name: str = Field(min_length=1, max_length=100)

class PredictRequest(BaseModel):
    records: list[dict[str, Any]] = Field(min_length=1, max_length=100)

class GenerateRequest(BaseModel):
    model: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=16000)
    system: str = Field(default='', max_length=8000)
    temperature: float = Field(default=0.7, ge=0, le=2)

class CompareRequest(BaseModel):
    experiment_ids: list[str] = Field(min_length=2, max_length=10)
    metric: str
