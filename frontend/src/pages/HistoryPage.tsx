import { useNavigate } from 'react-router-dom';
import { EmptyState, ErrorBanner, LoadingBlock } from '../components/common/Feedback';
import { PageHead } from '../components/common/PageHead';
import { StatusBadge } from '../components/common/Badge';
import { useHistory } from '../hooks/useHistory';
import { formatDateTime } from '../utils/format';

export function HistoryPage() {
  const navigate = useNavigate();
  const { items, loading, error, reload } = useHistory(50);

  return (
    <>
      <PageHead
        title="我的诊断历史"
        description="仅显示当前账号发起的诊断记录；他人的诊断对本账号不可见"
        extra={
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => void reload()} disabled={loading}>
            刷新
          </button>
        }
      />

      {error ? <ErrorBanner message={error} /> : null}

      <section className="card">
        {loading ? (
          <LoadingBlock text="正在加载历史记录…" />
        ) : items.length === 0 ? (
          <EmptyState text="暂无诊断记录，先到「智能诊断」发起一次诊断" icon="🗂" />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>报告编号</th>
                <th>设备</th>
                <th>诊断根因</th>
                <th>置信度</th>
                <th>状态</th>
                <th>生成时间</th>
                <th style={{ width: 90 }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.report_id}>
                  <td className="mono">{item.report_id}</td>
                  <td>{item.device_id ?? '—'}</td>
                  <td>{item.root_cause?.name ?? '—'}</td>
                  <td className="mono">
                    {typeof item.root_cause?.confidence === 'number'
                      ? item.root_cause.confidence.toFixed(2)
                      : '—'}
                  </td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>{formatDateTime(item.created_at)}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn--ghost btn--sm"
                      onClick={() => navigate('/report/' + item.report_id)}
                    >
                      查看
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </>
  );
}
