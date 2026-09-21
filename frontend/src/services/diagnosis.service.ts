import * as diagnosisApi from '../api/diagnosis';
import type {
  DiagnosisCard,
  DiagnosisOut,
  DeviceOption,
  HistoryItem,
  ReportResponse,
} from '../types/diagnosis';
import { clearLastThread, setLastThread } from '../utils/storage';

/** 会话在 UI 侧的统一视图：把后端三种状态归一化成页面可直接渲染的结构 */
export interface SessionView {
  threadId: string;
  phase: 'clarify' | 'review' | 'done';
  card: DiagnosisCard | null;
  deviceOptions: DeviceOption[];
  reportId: string | null;
  reportMarkdown: string | null;
  timings: Record<string, number>;
  errors: string[];
  degraded: boolean;
}

export function toSessionView(out: DiagnosisOut): SessionView {
  const card = out.payload?.card ?? out.card ?? null;
  const phase: SessionView['phase'] =
    out.status === 'awaiting_clarification' ? 'clarify'
      : out.status === 'awaiting_review' ? 'review'
        : 'done';
  return {
    threadId: out.thread_id,
    phase,
    card,
    deviceOptions: card?.options ?? [],
    reportId: out.report_id ?? null,
    reportMarkdown: out.report_markdown ?? null,
    timings: out.timings ?? {},
    errors: out.errors ?? [],
    degraded: Boolean(card?.degraded || (out.errors && out.errors.length > 0)),
  };
}

export const diagnosisService = {
  /** 发起一轮诊断（耗时较长，调用方需展示加载态） */
  async start(query: string, sessionId?: string): Promise<SessionView> {
    const out = await diagnosisApi.startDiagnosis(query, sessionId);
    setLastThread(out.thread_id);
    return toSessionView(out);
  },

  /** 澄清：补设备位号后继续诊断 */
  async clarify(threadId: string, deviceId: string): Promise<SessionView> {
    const out = await diagnosisApi.reviewDiagnosis({ thread_id: threadId, device_id: deviceId });
    return toSessionView(out);
  },

  /** 人工确认：生成报告并持久化 */
  async confirm(threadId: string, comment?: string): Promise<SessionView> {
    const out = await diagnosisApi.reviewDiagnosis({
      thread_id: threadId, decision: 'confirm', comment,
    });
    clearLastThread();
    return toSessionView(out);
  },

  history(limit = 20): Promise<HistoryItem[]> {
    return diagnosisApi.fetchHistory(limit);
  },

  report(reportId: string): Promise<ReportResponse> {
    return diagnosisApi.fetchReport(reportId);
  },

  sessionState(threadId: string): Promise<Record<string, unknown>> {
    return diagnosisApi.fetchSessionState(threadId);
  },
};
