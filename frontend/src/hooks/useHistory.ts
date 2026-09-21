import { useCallback, useEffect, useState } from 'react';
import { diagnosisService } from '../services/diagnosis.service';
import type { HistoryItem } from '../types/diagnosis';
import { ApiError } from '../types/common';

export function useHistory(limit = 20) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await diagnosisService.history(limit);
      setItems(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '加载历史记录失败');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { items, loading, error, reload };
}
