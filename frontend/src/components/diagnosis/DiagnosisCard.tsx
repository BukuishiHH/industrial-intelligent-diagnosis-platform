import type { DiagnosisCard as CardModel } from '../../types/diagnosis';
import { formatTimings } from '../../utils/format';
import { Badge } from '../common/Badge';
import { ConfidenceBar } from '../common/ConfidenceBar';

const URGENCY_TONE: Record<string, 'ok' | 'warn' | 'danger' | 'info'> = {
  运行观察: 'ok',
  计划停机: 'info',
  紧急停机: 'danger',
  立即停机: 'danger',
};

/**
 * 诊断结论卡片：字段全部来自后端结构化结论（A1 只做装配，不重新生成内容）。
 * 每一条证据都带定位标识，可回查手册原文或测点时间窗。
 */
export function DiagnosisCardView({
  card,
  timings,
  errorMessages,
  onConfirm,
  onReset,
  busy,
}: {
  card: CardModel;
  timings: Record<string, number>;
  errorMessages: string[];
  onConfirm: (comment?: string) => void;
  onReset: () => void;
  busy: boolean;
}) {
  const rootCause = card.root_cause ?? {};
  const manual = card.evidence_groups.find((group) => group.source === 'manual');
  const sensor = card.evidence_groups.find((group) => group.source === 'sensor');
  const confirmAction = card.actions.find((action) => action.key === 'confirm');
  const rejectAction = card.actions.find((action) => action.key === 'reject');

  return (
    <>
      <section className="summary-box">
        <div className="summary-box__label">诊断结论（待人工确认）</div>
        <div className="summary-box__text">{card.summary || '未形成明确结论'}</div>
        <div className="summary-box__meta">
          {card.urgency ? (
            <Badge tone={URGENCY_TONE[card.urgency] ?? 'info'}>处置紧迫度：{card.urgency}</Badge>
          ) : null}
          <span>{card.window_note}</span>
          <span className="mono">诊断编号 {card.diagnosis_id || '—'}</span>
        </div>
      </section>

      {card.degraded && errorMessages.length > 0 ? (
        <div className="alert alert--warn">
          本次诊断存在降级项：{errorMessages.join('；')}
        </div>
      ) : null}

      <section className="card">
        <h2 className="card__title">根本原因</h2>
        <div className="kv">
          <span className="kv__k">故障原因</span>
          <span className="kv__v" style={{ fontWeight: 700 }}>{rootCause.name || '未确定'}</span>
          <span className="kv__k">置信度</span>
          <span className="kv__v">
            <ConfidenceBar value={rootCause.confidence} />
          </span>
          <span className="kv__k">判定依据</span>
          <span className="kv__v">{rootCause.basis || '—'}</span>
        </div>
      </section>

      {card.candidate_alternatives.length > 0 ? (
        <section className="card">
          <h2 className="card__title">
            备选原因
            <span className="card__subtitle">已排除或置信度较低的可能性</span>
          </h2>
          <table className="table">
            <thead>
              <tr>
                <th>可能原因</th>
                <th style={{ width: 190 }}>置信度</th>
              </tr>
            </thead>
            <tbody>
              {card.candidate_alternatives.map((item) => (
                <tr key={item.name}>
                  <td>{item.name}</td>
                  <td>
                    <ConfidenceBar value={item.confidence} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <section className="card">
        <h2 className="card__title">
          证据链
          <span className="card__subtitle">每条证据均可回查来源</span>
        </h2>

        <div className="section-label">知识依据（设备手册）</div>
        {manual && manual.items.length > 0 ? (
          <ul className="evidence-list">
            {manual.items.map((item, index) => (
              <li className="evidence-item" key={'m' + index}>
                {item.locator ? <span className="evidence-item__locator">{item.locator}</span> : null}
                <div>{item.text}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="hint">（无手册依据）</p>
        )}

        <div className="section-label">数据依据（传感器实测）</div>
        {sensor && sensor.items.length > 0 ? (
          <ul className="evidence-list">
            {sensor.items.map((item, index) => (
              <li className="evidence-item evidence-item--sensor" key={'s' + index}>
                {item.locator ? <span className="evidence-item__locator">{item.locator}</span> : null}
                <div>{item.text}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="hint">（无实测数据依据）</p>
        )}
      </section>

      <section className="card">
        <h2 className="card__title">处置建议</h2>
        <ol className="steps">
          {card.solution_steps.map((step, index) => {
            const parts = step.split('　（依据：');
            return (
              <li key={'step' + index}>
                <div>{parts[0]}</div>
                {parts[1] ? <span className="steps__ref">依据：{parts[1].replace(/）$/, '')}</span> : null}
              </li>
            );
          })}
        </ol>
        {card.notes.length > 0 ? (
          <div className="alert alert--info mt-16">
            <strong>安全与提示：</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
              {card.notes.map((note, index) => (
                <li key={'note' + index}>{note}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      <section className="card">
        <div className="row row--between">
          <div className="timings">{formatTimings(timings)}</div>
          <div className="btn-row">
            <button type="button" className="btn btn--ghost" onClick={onReset} disabled={busy}>
              重新提问
            </button>
            <button
              type="button"
              className="btn btn--ghost"
              disabled
              title={rejectAction?.enabled === false ? '否定分支尚未开放（后续版本）' : ''}
            >
              {rejectAction?.label ?? '否定'}
            </button>
            <button
              type="button"
              className="btn btn--primary"
              disabled={busy || confirmAction?.enabled === false}
              onClick={() => onConfirm()}
            >
              {busy ? '生成报告中…' : '确认并生成报告'}
            </button>
          </div>
        </div>
        <p className="hint mt-8">
          确认后系统将生成 Markdown 诊断报告并持久化（记录审核人与时间）；AI 结论未经确认不会进入正式档案。
        </p>
      </section>
    </>
  );
}
