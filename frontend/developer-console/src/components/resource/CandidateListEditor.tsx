import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import type { ComparisonCandidate } from "@/types/api";

export const MIN_CANDIDATES = 2;

/**
 * Shared provider/model candidate editor for Compare and Benchmarks — the
 * backend requires at least two independently-evaluated candidates
 * (`Field(min_length=2)` on both CompareRequest and BenchmarkRunRequest).
 */
export function CandidateListEditor({
  candidates,
  onChange,
}: {
  candidates: ComparisonCandidate[];
  onChange: (candidates: ComparisonCandidate[]) => void;
}) {
  function updateCandidate(index: number, patch: Partial<ComparisonCandidate>) {
    onChange(candidates.map((candidate, i) => (i === index ? { ...candidate, ...patch } : candidate)));
  }

  function removeCandidate(index: number) {
    onChange(candidates.filter((_, i) => i !== index));
  }

  function addCandidate() {
    onChange([...candidates, { provider: "", model: "", model_version: "" }]);
  }

  return (
    <div className="space-y-3">
      {candidates.map((candidate, index) => (
        <div
          key={index}
          className="grid gap-3 rounded-[var(--radius-console)] border border-border bg-surface-raised/40 p-3 sm:grid-cols-[1fr_1fr_1fr_auto]"
        >
          <Field label="Provider" htmlFor={`candidate-${index}-provider`}>
            <Input
              id={`candidate-${index}-provider`}
              value={candidate.provider}
              placeholder="openai"
              onChange={(event) => updateCandidate(index, { provider: event.target.value })}
            />
          </Field>
          <Field label="Model" htmlFor={`candidate-${index}-model`}>
            <Input
              id={`candidate-${index}-model`}
              value={candidate.model}
              placeholder="model-id"
              onChange={(event) => updateCandidate(index, { model: event.target.value })}
            />
          </Field>
          <Field
            label="Model version"
            htmlFor={`candidate-${index}-version`}
            hint="Optional."
          >
            <Input
              id={`candidate-${index}-version`}
              value={candidate.model_version ?? ""}
              onChange={(event) => updateCandidate(index, { model_version: event.target.value })}
            />
          </Field>
          <div className="flex items-end">
            <Button
              type="button"
              variant="secondary"
              size="icon"
              aria-label={`Remove candidate ${index + 1}`}
              disabled={candidates.length <= MIN_CANDIDATES}
              onClick={() => removeCandidate(index)}
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </div>
      ))}
      <Button type="button" variant="secondary" size="sm" onClick={addCandidate}>
        <Plus className="h-4 w-4" aria-hidden="true" />
        Add candidate
      </Button>
    </div>
  );
}
