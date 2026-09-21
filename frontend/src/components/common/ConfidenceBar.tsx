import { confidenceLevel, formatConfidence } from '../../utils/format';

/** 置信度可视化：颜色随高/中/低变化，避免只看数字的误读 */
export function ConfidenceBar({ value, label }: { value: number | null | undefined; label?: string }) {
  const level = confidenceLevel(value);
  const percent = Math.max(0, Math.min(100, (value ?? 0) * 100));
  const fillClass = level === 'high' ? 'confidence__fill'
    : level === 'mid' ? 'confidence__fill confidence__fill--mid'
      : 'confidence__fill confidence__fill--low';
  return (
    <div className="confidence">
      {label ? <span className="kv__k">{label}</span> : null}
      <div className="confidence__bar">
        <div className={fillClass} style={{ width: percent + '%' }} />
      </div>
      <span className="confidence__num">{formatConfidence(value)}</span>
    </div>
  );
}
