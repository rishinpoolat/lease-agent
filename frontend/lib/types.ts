// Mirrors backend/api/app/schemas.py -- keep in sync by hand (no shared
// codegen for this build; see README "what I left out").

export type ReviewStatus = "pending" | "accepted" | "rejected" | "edited";
export type Confidence = "high" | "low" | "not_found";
export type Severity = "high" | "medium" | "low";
export type Verdict = "PASS" | "FAIL" | "NOT_DETERMINABLE";
export type UnitStatus = "available" | "occupied";
export type JobState = "queued" | "processing" | "done" | "failed";

export interface UnitSummary {
  unit_id: string;
  label: string;
  building_name: string;
  property_name: string;
  type: string;
  status: UnitStatus;
}

export interface LeaseField {
  id: string;
  field_name: string;
  value: unknown;
  confidence: Confidence;
  source_excerpt: string | null;
  review_status: ReviewStatus;
  edited_value: unknown;
}

export interface Flag {
  id: string;
  field_name: string | null;
  description: string;
  severity: Severity;
  review_status: ReviewStatus;
}

export interface RuleEvaluation {
  id: string;
  rule_id: string;
  verdict: Verdict;
  reason: string;
  severity: Severity;
  source_field_refs: string[];
}

export interface Lease {
  id: string;
  source_file_ref: string;
  uploaded_at: string;
  unit_match_accepted: boolean;
  fields: LeaseField[];
  flags: Flag[];
  rule_evaluations: RuleEvaluation[];
}

export interface WorkOrder {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  review_status: ReviewStatus;
}

export interface PhotoReport {
  id: string;
  uploaded_at: string;
  photo_refs: string[];
  condition_assessment: string | null;
  detected_contents: string[];
  damages: string[];
  work_orders: WorkOrder[];
}

export interface UnitDetail extends UnitSummary {
  lease: Lease | null;
  photo_reports: PhotoReport[];
}

export interface JobStatusResponse {
  id: string;
  type: string;
  status: JobState;
  error: string | null;
}

export interface UploadAccepted {
  job_id: string;
}
