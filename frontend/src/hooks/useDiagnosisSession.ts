import { useCallback, useEffect, useRef, useState } from 'react';
import { diagnosisService, type SessionView } from '../services/diagnosis.service';
import { ApiError } from '../types/common';

export type SessionPhase = 'idle' | 'running' | 'clarify' | 'review' | 'done';

/** 客户端阶段提示：后端为一次性返回，这里用计时器给出可感知的进度文案 */
const STAGE_HINTS: { after: number; text: string }[] = [
  { after: 0, text: '正在解析问题意图与设备位号…' },
  { after: 4, text: '正在检索设备手册知识库（向量 + 关键词）…' },
  { after: 12, text: '正在分析传感器数据与阈值趋势…' },
  { after: 16, text: '正在融合知识与数据证据进行推理…' },
  { after: 30, text: '模型仍在推理，请稍候（通常 20~40 秒）…' },
];

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 401) return '登录已失效，请重新登录';
    return error.message;
  }
  return error instanceof Error ? error.message : '未知错误';
}

export function useDiagnosisSession() {
  const [phase, setPhase] = useState<SessionPhase>('idle');
  const [view, setView] = useState<SessionView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [stageHint, setStageHint] = useState(STAGE_HINTS[0].text);
  const timerRef = useRef<number | null>(null);

  const stopTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    stopTimer();
    const began = Date.now();
    setElapsed(0);
    setStageHint(STAGE_HINTS[0].text);
    timerRef.current = window.setInterval(() => {
      const seconds = (Date.now() - began) / 1000;
      setElapsed(seconds);
      let text = STAGE_HINTS[0].text;
      for (const hint of STAGE_HINTS) {
        if (seconds >= hint.after) text = hint.text;
      }
      setStageHint(text);
    }, 500);
  }, [stopTimer]);

  useEffect(() => stopTimer, [stopTimer]);

  const run = useCallback(async (query: string) => {
    setError(null);
    setView(null);
    setPhase('running');
    startTimer();
    try {
      const next = await diagnosisService.start(query);
      setView(next);
      setPhase(next.phase);
    } catch (err) {
      setError(errorMessage(err));
      setPhase('idle');
    } finally {
      stopTimer();
    }
  }, [startTimer, stopTimer]);

  const chooseDevice = useCallback(async (deviceId: string) => {
    if (!view) return;
    setError(null);
    setPhase('running');
    startTimer();
    try {
      const next = await diagnosisService.clarify(view.threadId, deviceId);
      setView(next);
      setPhase(next.phase);
    } catch (err) {
      setError(errorMessage(err));
      setPhase('clarify');
    } finally {
      stopTimer();
    }
  }, [startTimer, stopTimer, view]);

  const confirm = useCallback(async (comment?: string) => {
    if (!view) return;
    setError(null);
    setPhase('running');
    startTimer();
    try {
      const next = await diagnosisService.confirm(view.threadId, comment);
      setView(next);
      setPhase('done');
    } catch (err) {
      setError(errorMessage(err));
      setPhase('review');
    } finally {
      stopTimer();
    }
  }, [startTimer, stopTimer, view]);

  const reset = useCallback(() => {
    stopTimer();
    setView(null);
    setError(null);
    setElapsed(0);
    setPhase('idle');
  }, [stopTimer]);

  return { phase, view, error, elapsed, stageHint, run, chooseDevice, confirm, reset };
}
