import type { DiagnosisOut, HistoryItem, ReportResponse, ReviewPayload } from '../types/diagnosis';
import { request } from './client';

/** 发起诊断：可能直接返回待审核卡片，也可能要求先澄清设备 */
export function startDiagnosis(query: string, sessionId?: string): Promise<DiagnosisOut> {
  return request<DiagnosisOut>('/diagnosis/query', {
    method: 'POST',
    body: { query, session_id: sessionId ?? null },
  });
}

/** 澄清回答（device_id）或人工审核（decision） */
export function reviewDiagnosis(payload: ReviewPayload): Promise<DiagnosisOut> {
  return request<DiagnosisOut>('/diagnosis/review', { method: 'POST', body: payload });
}

export function fetchReport(reportId: string): Promise<ReportResponse> {
  return request<ReportResponse>('/diagnosis/report/' + encodeURIComponent(reportId));
}

export function fetchHistory(limit = 20): Promise<HistoryItem[]> {
  return request<HistoryItem[]>('/diagnosis/history', { query: { limit } });
}

export function fetchSessionState(threadId: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>('/diagnosis/state/' + encodeURIComponent(threadId));
}
