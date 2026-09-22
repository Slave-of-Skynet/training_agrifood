export interface HealthResponse {
  status: "ok";
  service: "smart-harvest";
  analytics: "not_configured" | "ready" | "unavailable";
}

export type AssessmentStatus = "assessed" | "insufficient_data";
export type RiskBand = "low" | "moderate" | "high";

export interface RiskEstimate {
  score: number;
  band: RiskBand | null;
}

export interface DeteriorationHorizon {
  starts_at: string;
  ends_at: string | null;
}

export type FactorCategory =
  | "data_quality"
  | "environmental"
  | "storage"
  | "transport"
  | "inventory"
  | "historical";

export type FactorEffect = "increases_risk" | "decreases_risk" | "unknown";

export interface AssessmentFactor {
  code: string;
  category: FactorCategory;
  effect: FactorEffect;
  summary: string;
  evidence_references: string[];
}

export interface Recommendation {
  action_code: string;
  label: string;
  priority: "informational" | "low" | "medium" | "high";
  rationale_codes: string[];
  requires_human_review: boolean;
}

export interface Reliability {
  level: "unavailable" | "low" | "medium" | "high";
  confidence_score: number | null;
  reason_codes: string[];
  missing_requirements: string[];
}

export interface Provenance {
  contract_version: string;
  engine_tier: "fixture" | "deterministic_baseline" | "learned_model";
  engine_version: string;
  generated_at: string;
  source_dataset_id: string | null;
  simulation: boolean;
  notice: string;
}

export interface RiskAssessment {
  batch_id: string;
  status: AssessmentStatus;
  risk: RiskEstimate | null;
  deterioration_horizon: DeteriorationHorizon | null;
  factors: AssessmentFactor[];
  recommendation: Recommendation | null;
  reliability: Reliability;
  provenance: Provenance;
}

export interface RiskAssessmentCollectionResponse {
  items: RiskAssessment[];
  total_count: number;
  window_start: string;
  window_end: string;
  facility_id: string | null;
  engine_version: string;
}
