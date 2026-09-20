/** 与后端 packages/service/schemas.py、packages/schemas/diagnosis.py 对齐 */

export type SessionStatus = 'awaiting_clarification' | 'awaiting_review' | 'completed';

export interface CardAction {
  key: string;
  label: string;
  enabled: boolean;
}

export interface EvidenceItem {
  text: string;
  locator?: string | null;
  chart_ref?: string | null;
}

export interface EvidenceGroup {
  source: 'manual' | 'sensor';
  items: EvidenceItem[];
}

export interface RootCause {
  name?: string | null;
  confidence?: number | null;
  basis?: string | null;
}

export interface CandidateAlternative {
  name: string;
  confidence: number;
}

export interface DeviceOption {
  device_id: string;
  label: string;
}

export interface DiagnosisCard {
  type: 'diagnosis_card' | 'clarification_card' | 'message';
  summary: string;
  window_note: string;
  urgency: string;
  overall_confidence: number;
  root_cause: RootCause;
  evidence_groups: EvidenceGroup[];
  solution_steps: string[];
  candidate_alternatives: CandidateAlternative[];
  actions: CardAction[];
  diagnosis_id: string;
  degraded: boolean;
  notes: string[];
  options: DeviceOption[];
}

/** interrupt 载荷：澄清卡片或待审核卡片 */
export interface InterruptPayload {
  type: 'clarification_card' | 'diagnosis_card' | string;
  card: DiagnosisCard;
  diagnosis_id?: string;
}

export interface DiagnosisOut {
  thread_id: string;
  status: SessionStatus;
  payload?: InterruptPayload | null;
  diagnosis_id?: string | null;
  report_id?: string | null;
  report_markdown?: string | null;
  card?: DiagnosisCard | null;
  timings: Record<string, number>;
  errors: string[];
  search_trace: Record<string, unknown>;
}

export interface HistoryItem {
  report_id: string;
  diagnosis_id: string | null;
  device_id: string | null;
  root_cause: { code?: string; name?: string; confidence?: number } | null;
  chars: number | null;
  status: string | null;
  created_at: string;
  source: string;
}

export interface ReportRecord {
  diagnosis_id?: string;
  device_id?: string;
  device_model?: string;
  status?: string;
  window?: { start?: string; end?: string };
  root_cause?: { code?: string; name?: string; confidence?: number; basis?: string };
  urgency?: string;
  overall_confidence?: number;
  candidate_causes?: { name: string; confidence: number }[];
  threshold_hits?: string[];
  evidence_gaps?: string[];
  reviews?: { decision: string; reviewer_user_id?: number; comment?: string; decided_at?: string }[];
  created_at?: string;
  source?: string;
}

export interface ReportResponse {
  report_id: string;
  format: string;
  content: string;
  record: ReportRecord | null;
}

export interface ReviewPayload {
  thread_id: string;
  decision?: 'confirm' | 'reject';
  device_id?: string;
  comment?: string;
}
