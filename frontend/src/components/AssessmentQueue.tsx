import { useEffect, useState } from "react";

import { ApiError, getAssessmentCollection } from "../api/client";
import type { RiskAssessment, RiskAssessmentCollectionResponse } from "../api/contracts";

type QueueState =
  | { kind: "loading" }
  | { kind: "success"; collection: RiskAssessmentCollectionResponse }
  | { kind: "error"; unavailable: boolean };

interface AssessmentQueueProps {
  onSelect: (assessment: RiskAssessment) => void;
  selectedBatchId?: string;
}

export function AssessmentQueue({ onSelect, selectedBatchId }: AssessmentQueueProps) {
  const [state, setState] = useState<QueueState>({ kind: "loading" });
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    getAssessmentCollection(controller.signal)
      .then((collection) => {
        if (!controller.signal.aborted) setState({ kind: "success", collection });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          kind: "error",
          unavailable: error instanceof ApiError && error.status === 503,
        });
      });

    return () => controller.abort();
  }, [retryKey]);

  const retry = () => {
    setState({ kind: "loading" });
    setRetryKey((current) => current + 1);
  };

  return (
    <section className="panel queue-panel" aria-labelledby="queue-heading">
      <p className="eyebrow">Ranked replay queue</p>
      <h2 id="queue-heading">Priority Queue</h2>
      <p className="queue-explainer">
        Ordered by predicted loss severity. Batches with equal severity scores are tied;
        Batch ID is used only for deterministic ordering.
      </p>
      <p className="queue-score-note">
        Scores range from 0.00 to 1.00 and are used for prioritisation. A score is not a
        probability, confidence score, or guarantee of loss.
      </p>

      {state.kind === "loading" && (
        <div className="queue-message" aria-live="polite">
          <span className="spinner" aria-hidden="true" />
          <p>Loading priority queue…</p>
        </div>
      )}

      {state.kind === "error" && (
        <div className="queue-error" role="alert">
          <p>
            {state.unavailable
              ? "Analytics runtime unavailable."
              : "Priority queue could not be loaded."}
          </p>
          <button type="button" onClick={retry}>Try again</button>
        </div>
      )}

      {state.kind === "success" && (
        <>
          <dl className="queue-metadata">
            <div><dt>Replay window</dt><dd><time dateTime={state.collection.window_start}>{state.collection.window_start}</time> to <time dateTime={state.collection.window_end}>{state.collection.window_end}</time></dd></div>
            <div><dt>Total batches</dt><dd>{state.collection.total_count}</dd></div>
            <div><dt>Engine version</dt><dd>{state.collection.engine_version}</dd></div>
          </dl>

          {state.collection.items.length === 0 ? (
            <p className="queue-empty">No batches found in this replay window.</p>
          ) : (
            <>
              <p className="queue-provenance" role="note">
                {state.collection.items[0].provenance.notice}
              </p>
              <p className="queue-count">
                Showing {state.collection.items.length} of {state.collection.total_count}
              </p>
              <ul className="queue-list">
                {state.collection.items.map((assessment) => (
                  <li
                    key={assessment.batch_id}
                    className={assessment.batch_id === selectedBatchId ? "queue-row queue-row--selected" : "queue-row"}
                  >
                    <div className="queue-row-text">
                      <strong className="queue-batch-id">{assessment.batch_id}</strong>
                      <span className="queue-score-label">Predicted loss severity score</span>
                      <span className="queue-score">
                        {assessment.status === "assessed" && assessment.risk
                          ? assessment.risk.score.toFixed(4)
                          : "Unavailable"}
                      </span>
                    </div>
                    <button
                      type="button"
                      aria-label={`View assessment for ${assessment.batch_id}`}
                      onClick={() => onSelect(assessment)}
                    >
                      View assessment
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </section>
  );
}
