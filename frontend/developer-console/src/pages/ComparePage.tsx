import { useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";

import { InlineError } from "@/components/ErrorState";
import { PageHeader } from "@/components/PageHeader";
import { CandidateListEditor, MIN_CANDIDATES } from "@/components/resource/CandidateListEditor";
import { ComparisonResultCard } from "@/components/resource/ComparisonResultCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/field";
import { useCompare } from "@/hooks/queries";
import type { ComparisonCandidate } from "@/types/api";

const MODALITIES = ["text", "image", "video", "audio", "coding", "agent", "other"];
const ACTIVITY_TYPES = [
  "text_generation",
  "text_reasoning",
  "image_generation",
  "image_editing",
  "image_enhancement",
  "video_generation",
  "audio_generation",
  "speech_to_text",
  "vision",
  "code_generation",
  "code_review",
  "debugging",
  "test_generation",
  "code_refactoring",
  "coding_agent",
  "embedding",
  "rag",
  "classification",
  "agent_workflow",
];

export function ComparePage() {
  const [modality, setModality] = useState("text");
  const [activityType, setActivityType] = useState("text_generation");
  const [inputTokens, setInputTokens] = useState("2000");
  const [outputTokens, setOutputTokens] = useState("1000");
  const [candidates, setCandidates] = useState<ComparisonCandidate[]>([
    { provider: "", model: "", model_version: "" },
    { provider: "", model: "", model_version: "" },
  ]);

  const compare = useCompare();

  const canSubmit =
    candidates.length >= MIN_CANDIDATES &&
    candidates.every((c) => c.provider.trim() && c.model.trim()) &&
    !compare.isPending;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    compare.mutate({
      modality,
      activity_type: activityType,
      input_tokens: inputTokens ? Number(inputTokens) : undefined,
      output_tokens: outputTokens ? Number(outputTokens) : undefined,
      candidates: candidates.map((c) => ({
        provider: c.provider.trim(),
        model: c.model.trim(),
        model_version: c.model_version?.trim() || undefined,
      })),
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Compare"
        description="Evaluate one workload definition independently against multiple provider/model candidates. This is not a recommendation, a ranking, or a winner — each candidate is measured on its own; the trade-off is yours to weigh."
      />

      <Card>
        <CardHeader>
          <CardTitle>Workload definition</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Field label="Modality" htmlFor="compare-modality">
                <Select
                  id="compare-modality"
                  value={modality}
                  onChange={(event) => setModality(event.target.value)}
                >
                  {MODALITIES.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Activity type" htmlFor="compare-activity">
                <Select
                  id="compare-activity"
                  value={activityType}
                  onChange={(event) => setActivityType(event.target.value)}
                >
                  {ACTIVITY_TYPES.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Input tokens" htmlFor="compare-input-tokens" hint="Optional.">
                <Input
                  id="compare-input-tokens"
                  type="number"
                  min={0}
                  value={inputTokens}
                  onChange={(event) => setInputTokens(event.target.value)}
                />
              </Field>
              <Field label="Output tokens" htmlFor="compare-output-tokens" hint="Optional.">
                <Input
                  id="compare-output-tokens"
                  type="number"
                  min={0}
                  value={outputTokens}
                  onChange={(event) => setOutputTokens(event.target.value)}
                />
              </Field>
            </div>
            <p className="text-xs text-muted-foreground">
              Only the fields relevant to a text/token-based workload are shown here. The API
              accepts the full workload field set (image, video, audio, tool-call and duration
              quantities) documented in the OpenAPI reference — use the API Explorer for other
              modalities.
            </p>

            <div>
              <p className="mb-2 text-sm font-medium text-foreground">
                Candidates (at least {MIN_CANDIDATES})
              </p>
              <CandidateListEditor candidates={candidates} onChange={setCandidates} />
            </div>

            <InlineError error={compare.error} />

            <Button type="submit" disabled={!canSubmit}>
              {compare.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : null}
              Run comparison
            </Button>
          </form>
        </CardContent>
      </Card>

      {compare.data ? (
        <div className="space-y-4" data-testid="compare-results">
          <p className="text-xs text-muted-foreground">
            Comparison ID: <span className="font-mono">{compare.data.comparison_id}</span> —
            results below are shown in the exact order submitted, never reordered by impact.
          </p>
          {compare.data.results.map((result, index) => (
            <ComparisonResultCard key={index} result={result} index={index} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
