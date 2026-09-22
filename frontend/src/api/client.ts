import type { HealthResponse, RiskAssessment } from "./contracts";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message?: string) {
    super(message ?? `Backend returned HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const data = (await response.json()) as { detail?: string };
      if (typeof data?.detail === "string") {
        detail = data.detail;
      }
    } catch {
      // ignore json parse failure
    }
    throw new ApiError(response.status, detail ?? `Backend returned HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/v1/health", signal);
}

export function getDemoAssessment(signal?: AbortSignal): Promise<RiskAssessment> {
  return getJson<RiskAssessment>("/api/v1/demo/assessment", signal);
}

export function getAssessment(batchId: string, signal?: AbortSignal): Promise<RiskAssessment> {
  const encodedId = encodeURIComponent(batchId.trim());
  return getJson<RiskAssessment>(`/api/v1/assessments/${encodedId}`, signal);
}
