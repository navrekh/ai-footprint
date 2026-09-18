/**
 * Types mirroring the AI Footprint REST API contract
 * (backend/footprint-api/app/schemas). The backend is authoritative:
 * nothing here may add, rename, or reinterpret a field.
 */

export type ProjectStatus = "active" | "archived";
export type ApplicationStatus = "active" | "inactive";
export type ApplicationEnvironment = "development" | "staging" | "production";
export type ApiKeyStatus = "active" | "revoked";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string | null;
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
  status?: ProjectStatus;
}

export interface Application {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  environment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  name: string;
  description?: string | null;
  environment?: ApplicationEnvironment | null;
  /** Required when authenticating with an organization-level API key. */
  project_id?: string | null;
}

export interface ApplicationUpdate {
  name?: string;
  description?: string | null;
  status?: ApplicationStatus;
  environment?: ApplicationEnvironment | null;
}

export interface ApiKey {
  id: string;
  organization_id: string;
  project_id: string | null;
  key_prefix: string;
  name: string;
  status: string;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
}

/** Raw key material — returned by the API exactly once, at creation time. */
export interface ApiKeyCreated {
  id: string;
  key: string;
  key_prefix: string;
  name: string;
}

export interface ApiKeyCreateRequest {
  name: string;
  project_id?: string | null;
  expires_at?: string | null;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
}

export interface ListParams {
  limit?: number;
  offset?: number;
}

// ---------------------------------------------------------------------------
// Shared resource-impact primitives (backend/footprint-api/app/schemas/common.py)
// ---------------------------------------------------------------------------

export type MetricStatus = "ok" | "partial" | "insufficient_data";
export type Confidence = "high" | "medium" | "low";
export type NormalizationBasis =
  | "input_plus_output"
  | "image_count"
  | "video_seconds"
  | "audio_minutes";
export type UsageGranularity = "day" | "week" | "month";

/** A single metric's range. min/max are absent exactly when status is insufficient_data. */
export interface MetricRange {
  status: MetricStatus;
  min: number | null;
  max: number | null;
  unit: string;
}

/** A metric range aggregated across multiple workloads, with explicit completeness. */
export interface AggregateMetricRange extends MetricRange {
  total_workloads: number;
  measured_workloads: number;
}

export interface Denominator {
  value: number;
  unit: string;
  basis: NormalizationBasis;
}

export interface NormalizedMetricRange {
  status: MetricStatus;
  min: number | null;
  max: number | null;
  unit: string;
  confidence: Confidence | null;
  evidence_level: number | null;
  methodology_version: string | null;
  accounting_boundary: string | null;
}

export interface NormalizedResourceIntensity {
  denominator: Denominator;
  energy: NormalizedMetricRange | null;
  water: NormalizedMetricRange | null;
  carbon: NormalizedMetricRange | null;
}

export interface ErrorDetail {
  code: string;
  message: string;
  request_id: string;
}

export interface ComparisonCandidate {
  provider: string;
  model: string;
  model_version?: string | null;
}

// ---------------------------------------------------------------------------
// Usage intelligence (backend/footprint-api/app/schemas/usage.py)
// ---------------------------------------------------------------------------

export interface UsagePeriod {
  from: string;
  to: string;
}

/** measured + partial + insufficient_data always sum to total. */
export interface WorkloadCounts {
  total: number;
  measured: number;
  partial: number;
  insufficient_data: number;
  coverage_percent: number;
}

export interface UsageFilterParams {
  from?: string;
  to?: string;
  project?: string | null;
  application?: string | null;
  provider?: string | null;
  model?: string | null;
  activity_type?: string | null;
}

export interface UsageSummary {
  period: UsagePeriod;
  workloads: WorkloadCounts;
  energy: AggregateMetricRange;
  water: AggregateMetricRange;
  carbon: AggregateMetricRange;
}

export interface UsageByProviderItem {
  provider: string;
  workloads: WorkloadCounts;
  energy: AggregateMetricRange;
  water: AggregateMetricRange;
  carbon: AggregateMetricRange;
}

export interface UsageByProviderResponse {
  period: UsagePeriod;
  items: UsageByProviderItem[];
  total: number;
}

export interface UsageByModelItem {
  provider: string;
  model: string;
  model_version: string | null;
  workloads: WorkloadCounts;
  energy: AggregateMetricRange;
  water: AggregateMetricRange;
  carbon: AggregateMetricRange;
}

export interface UsageByModelResponse {
  period: UsagePeriod;
  items: UsageByModelItem[];
  total: number;
}

export interface UsageByActivityItem {
  activity_type: string;
  workloads: WorkloadCounts;
  energy: AggregateMetricRange;
  water: AggregateMetricRange;
  carbon: AggregateMetricRange;
}

export interface UsageByActivityResponse {
  period: UsagePeriod;
  items: UsageByActivityItem[];
  total: number;
}

export interface UsageByApplicationItem {
  application_id: string;
  application_name: string;
  project_id: string;
  workloads: WorkloadCounts;
  energy: AggregateMetricRange;
  water: AggregateMetricRange;
  carbon: AggregateMetricRange;
}

export interface UsageByApplicationResponse {
  period: UsagePeriod;
  items: UsageByApplicationItem[];
  total: number;
}

export interface UsageTimeseriesPoint {
  period_start: string;
  workloads: WorkloadCounts;
  energy: AggregateMetricRange;
  water: AggregateMetricRange;
  carbon: AggregateMetricRange;
}

export interface UsageTimeseriesResponse {
  period: UsagePeriod;
  granularity: string;
  items: UsageTimeseriesPoint[];
}

// ---------------------------------------------------------------------------
// Estimates (backend/footprint-api/app/schemas/estimate.py) — as embedded in
// comparison/benchmark results, never fetched standalone by the console.
// ---------------------------------------------------------------------------

export interface EstimateResponse {
  estimate_id: string;
  energy: MetricRange;
  water: MetricRange;
  carbon: MetricRange;
  confidence: Confidence | null;
  evidence_level: number | null;
  accounting_boundary: string | null;
  methodology_version: string | null;
  assumptions: string[];
  created_at: string;
}

// ---------------------------------------------------------------------------
// Compare (backend/footprint-api/app/schemas/compare.py)
// ---------------------------------------------------------------------------

export interface CompareRequest {
  modality: string;
  activity_type: string;
  input_tokens?: number | null;
  output_tokens?: number | null;
  input_characters?: number | null;
  output_characters?: number | null;
  image_count?: number | null;
  image_width?: number | null;
  image_height?: number | null;
  video_seconds?: number | null;
  video_resolution?: string | null;
  audio_seconds?: number | null;
  tool_calls?: number | null;
  duration_seconds?: number | null;
  duration_ms?: number | null;
  metadata?: Record<string, unknown> | null;
  candidates: ComparisonCandidate[];
}

/** One candidate's independent outcome. Never ranked, scored, or reordered. */
export interface ComparisonResultItem {
  candidate: ComparisonCandidate;
  status: "success" | "failed";
  resolved: ComparisonCandidate | null;
  estimate: EstimateResponse | null;
  normalized: NormalizedResourceIntensity | null;
  error: ErrorDetail | null;
}

export interface CompareResponse {
  comparison_id: string;
  modality: string;
  activity_type: string;
  results: ComparisonResultItem[];
}

// ---------------------------------------------------------------------------
// Benchmarks (backend/footprint-api/app/schemas/benchmark.py)
// ---------------------------------------------------------------------------

export interface BenchmarkDefinition {
  benchmark_id: string;
  version: string;
  name: string;
  description: string;
  activity_type: string;
  modality: string;
  parameters: Record<string, unknown>;
}

export interface BenchmarkListResponse {
  items: BenchmarkDefinition[];
  total: number;
}

export interface BenchmarkRunRequest {
  benchmark_id: string;
  candidates: ComparisonCandidate[];
}

export interface BenchmarkRunResponse {
  benchmark_id: string;
  benchmark_version: string;
  modality: string;
  activity_type: string;
  results: ComparisonResultItem[];
}

// ---------------------------------------------------------------------------
// Methodology registry (backend/footprint-api/app/schemas/methodology.py) —
// GET /v1/methodology returns a bare array, not a {items,total} wrapper.
// ---------------------------------------------------------------------------

export interface Methodology {
  id: string;
  version: string;
  description: string;
  effective_date: string;
  sources: string[];
  assumptions: string[];
  limitations: string[];
  created_at: string;
}
