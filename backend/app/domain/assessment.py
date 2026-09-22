"""Typed output contracts for future assessment implementations.

These models describe application output only. They intentionally do not define
the unknown raw challenge input schema or implement analytics.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from app.domain._contract import ContractModel


class HealthResponse(ContractModel):
    status: Literal["ok"]
    service: Literal["smart-harvest"]
    analytics: Literal["not_configured", "ready", "unavailable"]


class AssessmentStatus(str, Enum):
    ASSESSED = "assessed"
    INSUFFICIENT_DATA = "insufficient_data"


class RiskBand(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class RiskEstimate(ContractModel):
    score: float = Field(ge=0.0, le=1.0)
    band: RiskBand | None = None


class DeteriorationHorizon(ContractModel):
    starts_at: datetime
    ends_at: datetime | None = None


class FactorCategory(str, Enum):
    DATA_QUALITY = "data_quality"
    ENVIRONMENTAL = "environmental"
    STORAGE = "storage"
    TRANSPORT = "transport"
    INVENTORY = "inventory"
    HISTORICAL = "historical"


class FactorEffect(str, Enum):
    INCREASES_RISK = "increases_risk"
    DECREASES_RISK = "decreases_risk"
    UNKNOWN = "unknown"


class AssessmentFactor(ContractModel):
    code: str = Field(min_length=1)
    category: FactorCategory
    effect: FactorEffect
    summary: str = Field(min_length=1)
    evidence_references: list[str] = Field(default_factory=list)


class RecommendationPriority(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(ContractModel):
    action_code: str = Field(min_length=1)
    label: str = Field(min_length=1)
    priority: RecommendationPriority
    rationale_codes: list[str] = Field(default_factory=list)
    requires_human_review: bool = True


class ReliabilityLevel(str, Enum):
    UNAVAILABLE = "unavailable"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Reliability(ContractModel):
    level: ReliabilityLevel
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)


class Provenance(ContractModel):
    contract_version: str = Field(min_length=1)
    engine_tier: Literal["fixture", "deterministic_baseline", "learned_model"]
    engine_version: str = Field(min_length=1)
    generated_at: datetime
    source_dataset_id: str | None = None
    simulation: bool
    notice: str = Field(min_length=1)


class RiskAssessment(ContractModel):
    batch_id: str = Field(min_length=1)
    status: AssessmentStatus
    risk: RiskEstimate | None = None
    deterioration_horizon: DeteriorationHorizon | None = None
    factors: list[AssessmentFactor] = Field(default_factory=list)
    recommendation: Recommendation | None = None
    reliability: Reliability
    provenance: Provenance

    @model_validator(mode="after")
    def enforce_status_semantics(self) -> "RiskAssessment":
        if self.status is AssessmentStatus.INSUFFICIENT_DATA:
            if self.risk is not None or self.deterioration_horizon is not None:
                raise ValueError(
                    "insufficient_data assessments cannot claim risk or a "
                    "deterioration horizon"
                )
        elif self.risk is None:
            raise ValueError("assessed assessments require a risk estimate")
        return self


class RiskAssessmentCollectionResponse(ContractModel):
    items: list[RiskAssessment]
    total_count: int
    window_start: datetime
    window_end: datetime
    facility_id: str | None
    engine_version: str
