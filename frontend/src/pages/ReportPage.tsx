import { useNavigate, useParams } from 'react-router-dom';
import { EmptyState, ErrorBanner, LoadingBlock } from '../components/common/Feedback';
import { PageHead } from '../components/common/PageHead';
import { StatusBadge } from '../components/common/Badge';
import { MarkdownReport } from '../components/report/MarkdownReport';
import { useReport } from '../hooks/useReport';
import { formatDateTime } from '../utils/format';

export function ReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const { report, loading, error } = useReport(reportId);

  const download = () => {
    if (!report) return;
    const blob = new Blob([report.content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = report.report_id + '.md';
    link.click();
    URL.revokeObjectURL(url);
  };

  const record = report?.record ?? null;

  return (
    <>
      <PageHead
        title="诊断报告"
        description={reportId ? '报告编号 ' + reportId : ''}
        extra={
          <>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => navigate(-1)}>
              返回
            </button>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => window.print()}>
              打印
            </button>
            <button type="button" className="btn btn--primary btn--sm" onClick={download} disabled={!report}>
              下载 Markdown
            </button>
          </>
        }
      />

      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <LoadingBlock text="正在加载报告…" /> : null}

      {!loading && !report && !error ? (
        <EmptyState text="报告不存在或已被删除" icon="📄" />
      ) : null}

      {report ? (
        <>
          {record ? (
            <section className="card card--tight">
              <div className="row" style={{ gap: 22 }}>
                <span>
                  <span className="kv__k">设备　</span>
                  {record.device_id ?? '—'}
                  {record.device_model ? '（' + record.device_model + '）' : ''}
                </span>
                <span>
                  <span className="kv__k">状态　</span>
                  <StatusBadge status={record.status} />
                </span>
                <span>
                  <span className="kv__k">根因　</span>
                  {record.root_cause?.name ?? '—'}
                </span>
                <span>
                  <span className="kv__k">处置　</span>
                  {record.urgency ?? '—'}
                </span>
                <span>
                  <span className="kv__k">生成　</span>
                  {formatDateTime(record.created_at)}
                </span>
                <span className="hint">数据来源：{record.source === 'database' ? '数据库' : '本地文件'}</span>
              </div>
            </section>
          ) : null}

          <MarkdownReport content={report.content} />
        </>
      ) : null}
    </>
  );
}
