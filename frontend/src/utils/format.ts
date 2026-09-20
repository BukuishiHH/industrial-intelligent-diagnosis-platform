/** 展示层格式化工具 */

export function formatPercent(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return '—';
  return (value * 100).toFixed(digits) + '%';
}

export function formatConfidence(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return value.toFixed(2);
}

export function confidenceLevel(value: number | null | undefined): 'high' | 'mid' | 'low' {
  if (value === null || value === undefined) return 'low';
  if (value >= 0.7) return 'high';
  if (value >= 0.4) return 'mid';
  return 'low';
}

export function formatDateTime(input: string | null | undefined): string {
  if (!input) return '—';
  const normalized = input.replace(' ', 'T');
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return input;
  const pad = (n: number) => String(n).padStart(2, '0');
  return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate())
    + ' ' + pad(date.getHours()) + ':' + pad(date.getMinutes());
}

/** 把节点耗时（秒）渲染成一行紧凑文本 */
export function formatTimings(timings: Record<string, number> | null | undefined): string {
  if (!timings) return '';
  const order = ['a1', 'a2', 'a3', 'a4', 'a5'];
  const parts: string[] = [];
  let total = 0;
  for (const key of order) {
    const value = timings[key];
    if (typeof value === 'number') {
      parts.push(key.toUpperCase() + ' ' + value.toFixed(1) + 's');
      total += value;
    }
  }
  if (parts.length === 0) return '';
  return parts.join(' · ') + '　合计 ' + total.toFixed(1) + 's';
}

export function truncate(text: string, max = 80): string {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '…' : text;
}
