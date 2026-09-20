import type { DiagnosisCard } from '../../types/diagnosis';

/** 澄清卡片：缺设备位号时强制让用户选择（后端不会猜测机组） */
export function ClarificationPanel({
  card,
  onChoose,
  disabled,
}: {
  card: DiagnosisCard;
  onChoose: (deviceId: string) => void;
  disabled: boolean;
}) {
  return (
    <section className="card">
      <h2 className="card__title">需要确认设备位号</h2>
      <p className="hint mt-0">{card.summary}</p>
      <div className="option-list">
        {card.options.map((option) => (
          <button
            key={option.device_id}
            type="button"
            className="option-btn"
            disabled={disabled}
            onClick={() => onChoose(option.device_id)}
          >
            <span>{option.label}</span>
            <span className="option-btn__id">{option.device_id}</span>
          </button>
        ))}
      </div>
      {card.notes.length > 0 ? (
        <div className="alert alert--info mt-16">{card.notes.join('；')}</div>
      ) : null}
    </section>
  );
}
