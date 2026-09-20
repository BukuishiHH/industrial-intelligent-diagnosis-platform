import { useState } from 'react';

/** 演示用示例问题：与仿真数据集场景一一对应 */
export const SAMPLE_QUERIES: { label: string; query: string; scenario: string }[] = [
  { label: '振动持续上升', query: 'FJ-01 最近振动一直往上涨，是什么原因？', scenario: 'unbalance_fj01' },
  { label: '振动突然跃升', query: 'FJ-01 今天振动突然跳起来了', scenario: 'rub_fj01' },
  { label: '瓦温偏高', query: '3 号机瓦温有点高，帮我看看', scenario: 'watemp_fj03' },
  { label: '运行是否正常', query: 'FJ-02 现在运行正常吗', scenario: 'normal' },
];

export function QueryForm({
  onSubmit,
  disabled,
}: {
  onSubmit: (query: string) => void;
  disabled: boolean;
}) {
  const [query, setQuery] = useState('');

  const submit = () => {
    const text = query.trim();
    if (!text || disabled) return;
    onSubmit(text);
  };

  return (
    <section className="card">
      <h2 className="card__title">
        描述设备问题
        <span className="card__subtitle">用现场语言提问即可，不需要懂系统</span>
      </h2>
      <div className="field">
        <textarea
          className="textarea"
          placeholder="例如：FJ-01 最近振动一直往上涨，是什么原因？"
          value={query}
          disabled={disabled}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) submit();
          }}
        />
      </div>
      <div className="btn-row">
        <button type="button" className="btn btn--primary" onClick={submit} disabled={disabled || !query.trim()}>
          {disabled ? '诊断中…' : '开始诊断'}
        </button>
        <span className="hint">Ctrl + Enter 快速提交</span>
      </div>
      <div className="section-label">示例问题</div>
      <div className="btn-row">
        {SAMPLE_QUERIES.map((item) => (
          <button
            key={item.scenario}
            type="button"
            className="btn btn--ghost btn--sm"
            disabled={disabled}
            onClick={() => setQuery(item.query)}
          >
            {item.label}
          </button>
        ))}
      </div>
    </section>
  );
}
