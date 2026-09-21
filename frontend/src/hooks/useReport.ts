import { useCallback, useEffect, useState } from 'react';
import { diagnosisService } from '../services/diagnosis.service';
import type { ReportResponse } from '../types/diagnosis';
import { ApiError } from '../types/common';

export function useReport(reportId: string | undefined) {
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(reportId));
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!reportId) {
      setReport(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setReport(await diagnosisService.report(reportId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '加载报告失败');
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { report, loading, error, reload };
}
