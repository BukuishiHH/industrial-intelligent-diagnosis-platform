import type { ReactNode } from 'react';

export type BadgeTone = 'default' | 'ok' | 'warn' | 'danger' | 'info';

export function Badge({ tone = 'default', children }: { tone?: BadgeTone; children: ReactNode }) {
  const cls = tone === 'default' ? 'badge' : 'badge badge--' + tone;
  return <span className={cls}>{children}</span>;
}

/** 诊断记录状态徽章（与后端状态机一致） */
export function StatusBadge({ status }: { status: string | null | undefined }) {
  const map: Record<string, { tone: BadgeTone; text: string }> = {
    PENDING_REVIEW: { tone: 'warn', text: '待审核' },
    CONFIRMED: { tone: 'info', text: '已确认' },
    REPORTED: { tone: 'ok', text: '已出报告' },
    REJECTED: { tone: 'danger', text: '已否定' },
  };
  const item = map[status ?? ''] ?? { tone: 'default' as BadgeTone, text: status || '未知' };
  return <Badge tone={item.tone}>{item.text}</Badge>;
}
