import { useState, type FormEvent } from "react";

interface BatchAssessmentLookupProps {
  onSubmit: (batchId: string) => void;
  isLoading: boolean;
}

export function BatchAssessmentLookup({ onSubmit, isLoading }: BatchAssessmentLookupProps) {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) {
      return;
    }
    onSubmit(trimmed);
  };

  return (
    <section className="panel lookup-panel" aria-labelledby="lookup-heading">
      <p className="eyebrow">Single-batch lookup</p>
      <h2 id="lookup-heading">Evaluate Batch</h2>
      <form onSubmit={handleSubmit} className="lookup-form">
        <div className="lookup-field">
          <label htmlFor="batch-id-input" className="lookup-label">
            Batch ID
          </label>
          <input
            id="batch-id-input"
            type="text"
            className="lookup-input"
            placeholder="e.g. BAT-000901"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        <button
          type="submit"
          className="lookup-button"
          disabled={isLoading || !inputValue.trim()}
        >
          {isLoading ? "Loading…" : "Load assessment"}
        </button>
      </form>
    </section>
  );
}
