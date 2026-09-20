import { useNavigate } from 'react-router-dom';
import { ClarificationPanel } from '../components/diagnosis/ClarificationPanel';
import { DiagnosisCardView } from '../components/diagnosis/DiagnosisCard';
import { QueryForm } from '../components/diagnosis/QueryForm';
import { RunningIndicator } from '../components/diagnosis/RunningIndicator';
import { ErrorBanner, InfoBanner } from '../components/common/Feedback';
import { PageHead } from '../components/common/PageHead';
import { useDiagnosisSession } from '../hooks/useDiagnosisSession';

export function DiagnosisPage() {
  const navigate = useNavigate();
  const { phase, view, error, elapsed, stageHint, run, chooseDevice, confirm, reset } = useDiagnosisSession();
  const busy = phase === 'running';

  return (
    <>
      <PageHead
        title="智能诊断"
        description="以设备手册知识为依据、以传感器数据为证据，输出可溯源的故障原因与处置建议"
      />

      {error ? <ErrorBanner message={error} /> : null}

      {phase === 'idle' || phase === 'done' ? (
        <QueryForm onSubmit={(query) => void run(query)} disabled={busy} />
      ) : null}

      {busy ? <RunningIndicator stageHint={stageHint} elapsed={elapsed} /> : null}

      {phase === 'clarify' && view?.card ? (
        <ClarificationPanel card={view.card} disabled={busy} onChoose={(deviceId) => void chooseDevice(deviceId)} />
      ) : null}

      {phase === 'review' && view?.card ? (
        <DiagnosisCardView
          card={view.card}
          timings={view.timings}
          errorMessages={view.errors}
          busy={busy}
          onConfirm={(comment) => void confirm(comment)}
          onReset={reset}
        />
      ) : null}

      {phase === 'done' && view ? (
        <>
          <InfoBanner>
            报告已生成并持久化，编号 <strong className="mono">{view.reportId}</strong>。
            报告中的每条证据均可回溯到设备手册原文或传感器实测数据。
          </InfoBanner>
          <div className="btn-row">
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => navigate('/report/' + view.reportId)}
            >
              查看诊断报告
            </button>
            <button type="button" className="btn btn--ghost" onClick={reset}>
              再诊断一台设备
            </button>
            <button type="button" className="btn btn--ghost" onClick={() => navigate('/history')}>
              查看历史记录
            </button>
          </div>
        </>
      ) : null}
    </>
  );
}
