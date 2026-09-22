import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, getAssessment, getHealth } from "../api/client";
import type { HealthResponse, RiskAssessment } from "../api/contracts";
import { AssessmentCard } from "../components/AssessmentCard";
import { AssessmentQueue } from "../components/AssessmentQueue";
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
  const [selectedQueueBatchId, setSelectedQueueBatchId] = useState<string>();
  const manualRequest = useRef<AbortController | null>(null);

  useEffect(() => () => manualRequest.current?.abort(), []);

  const retryHealth = useCallback(() => {
    manualRequest.current?.abort();
    manualRequest.current = null;
    setAssessmentState({ kind: "idle" });
    setSelectedQueueBatchId(undefined);
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

    manualRequest.current?.abort();
    const controller = new AbortController();
    manualRequest.current = controller;
    setSelectedQueueBatchId(undefined);
    setAssessmentState({ kind: "loading", batchId: trimmed });

    getAssessment(trimmed, controller.signal)
      .then((assessment) => {
        if (controller.signal.aborted) return;
        setAssessmentState({ kind: "success", assessment });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
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
      })
      .finally(() => {
        if (manualRequest.current === controller) manualRequest.current = null;
      });
  }, []);

  const handleQueueSelect = useCallback((assessment: RiskAssessment) => {
    manualRequest.current?.abort();
    manualRequest.current = null;
    setSelectedQueueBatchId(assessment.batch_id);
    setAssessmentState({ kind: "success", assessment });
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
        <div className="workspace-grid">
          <div className="workspace-queue">
            {healthConnection.health.analytics === "ready" ? (
              <AssessmentQueue
                onSelect={handleQueueSelect}
                selectedBatchId={selectedQueueBatchId}
              />
            ) : (
              <section className="panel queue-panel" aria-labelledby="queue-heading">
                <p className="eyebrow">Ranked replay queue</p>
                <h2 id="queue-heading">Priority Queue</h2>
                <p className="status-note">
                  The priority queue is available when analytics is ready.
                </p>
              </section>
            )}
          </div>

          <div className="workspace-detail">
            {assessmentState.kind === "idle" && (
              <section className="panel assessment-idle-panel" aria-labelledby="idle-heading">
                <p className="eyebrow">Batch Review</p>
                <h2 id="idle-heading">Select a batch to review</h2>
                <p className="status-note">
                  Select a batch from the priority queue or use the single-batch lookup.
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

          <div className="workspace-lookup">
            <BatchAssessmentLookup
              onSubmit={handleLookup}
              isLoading={assessmentState.kind === "loading"}
            />
          </div>

          <aside className="workspace-status">
            <BackendStatus health={healthConnection.health} />
          </aside>
        </div>
      )}
    </main>
  );
}
