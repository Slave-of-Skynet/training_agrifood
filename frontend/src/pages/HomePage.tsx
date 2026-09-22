import { useCallback, useEffect, useState } from "react";

import { ApiError, getAssessment, getHealth } from "../api/client";
import type { HealthResponse, RiskAssessment } from "../api/contracts";
import { AssessmentCard } from "../components/AssessmentCard";
import { BackendStatus } from "../components/BackendStatus";
import { BatchAssessmentLookup } from "../components/BatchAssessmentLookup";

type HealthConnectionState =
  | { kind: "loading" }
  | { kind: "available"; health: HealthResponse }
  | { kind: "unavailable"; message: string };

type AssessmentRequestState =
  | { kind: "idle" }
  | { kind: "loading"; batchId: string }
  | { kind: "success"; assessment: RiskAssessment }
  | { kind: "error"; batchId: string; status?: number; message: string };

export function HomePage() {
  const [healthConnection, setHealthConnection] = useState<HealthConnectionState>({
    kind: "loading",
  });
  const [assessmentState, setAssessmentState] = useState<AssessmentRequestState>({
    kind: "idle",
  });
  const [reloadKey, setReloadKey] = useState(0);

  const retryHealth = useCallback(() => {
    setHealthConnection({ kind: "loading" });
    setReloadKey((current) => current + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    getHealth(controller.signal)
      .then((health) => {
        setHealthConnection({ kind: "available", health });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message = error instanceof Error ? error.message : "Unknown connection error";
        setHealthConnection({ kind: "unavailable", message });
      });

    return () => controller.abort();
  }, [reloadKey]);

  const handleLookup = useCallback((batchId: string) => {
    const trimmed = batchId.trim();
    if (!trimmed) return;

    setAssessmentState({ kind: "loading", batchId: trimmed });

    getAssessment(trimmed)
      .then((assessment) => {
        setAssessmentState({ kind: "success", assessment });
      })
      .catch((error: unknown) => {
        if (error instanceof ApiError) {
          setAssessmentState({
            kind: "error",
            batchId: trimmed,
            status: error.status,
            message: error.message,
          });
        } else {
          const message = error instanceof Error ? error.message : "Assessment request failed";
          setAssessmentState({
            kind: "error",
            batchId: trimmed,
            message,
          });
        }
      });
  }, []);

  return (
    <main className="app-shell">
      <header className="hero">
        <p className="eyebrow">Operator Decision Support</p>
        <h1>Smart Harvest</h1>
        <p>
          Dispatch-time decision support for reviewing batch assessments and
          prioritising attention where a validated score is available.
        </p>
      </header>

      {healthConnection.kind === "loading" && (
        <section className="panel connection-state" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          <div>
            <p className="eyebrow">System status</p>
            <h2>Connecting…</h2>
          </div>
        </section>
      )}

      {healthConnection.kind === "unavailable" && (
        <section className="panel connection-state connection-state--error" aria-live="polite">
          <div>
            <p className="eyebrow">System status</p>
            <h2>Unavailable</h2>
            <p>The application could not reach the Smart Harvest API: {healthConnection.message}</p>
          </div>
          <button type="button" onClick={retryHealth}>
            Try again
          </button>
        </section>
      )}

      {healthConnection.kind === "available" && (
        <div className="content-grid">
          <div className="workspace-main">
            <BatchAssessmentLookup
              onSubmit={handleLookup}
              isLoading={assessmentState.kind === "loading"}
            />

            {assessmentState.kind === "idle" && (
              <section className="panel assessment-idle-panel" aria-labelledby="idle-heading">
                <p className="eyebrow">Batch Review</p>
                <h2 id="idle-heading">No batch loaded</h2>
                <p className="status-note">
                  Enter a Batch ID above and select &ldquo;Load assessment&rdquo; to review an assessment.
                </p>
              </section>
            )}

            {assessmentState.kind === "loading" && (
              <section className="panel assessment-loading-panel" aria-live="polite">
                <span className="spinner" aria-hidden="true" />
                <div>
                  <p className="eyebrow">Batch Review</p>
                  <h2>Loading assessment…</h2>
                  <p className="batch-id">Batch: {assessmentState.batchId}</p>
                </div>
              </section>
            )}

            {assessmentState.kind === "error" && (
              <section className="panel assessment-error-panel" role="alert" aria-labelledby="error-heading">
                <p className="eyebrow">Batch Review</p>
                <h2 id="error-heading">Assessment unavailable</h2>
                <p className="batch-id">Batch: {assessmentState.batchId}</p>

                <div className="assessment-error-message">
                  {assessmentState.status === 404 && (
                    <p className="error-text">Batch not found.</p>
                  )}
                  {assessmentState.status === 409 && (
                    <p className="error-text">This batch is not eligible for this assessment release.</p>
                  )}
                  {assessmentState.status === 503 && (
                    <p className="error-text">Analytics runtime unavailable.</p>
                  )}
                  {assessmentState.status !== 404 &&
                    assessmentState.status !== 409 &&
                    assessmentState.status !== 503 && (
                      <p className="error-text">{assessmentState.message || "Assessment could not be completed."}</p>
                    )}
                </div>
              </section>
            )}

            {assessmentState.kind === "success" && (
              <AssessmentCard assessment={assessmentState.assessment} />
            )}
          </div>

          <aside className="workspace-aside">
            <BackendStatus health={healthConnection.health} />
          </aside>
        </div>
      )}
    </main>
  );
}
