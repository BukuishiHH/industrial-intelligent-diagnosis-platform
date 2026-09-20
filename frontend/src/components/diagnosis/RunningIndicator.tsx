import { LoadingBlock } from '../common/Feedback';

/** 诊断进行中的提示：后端一次性返回结果，这里给出可感知的阶段进度 */
export function RunningIndicator({ stageHint, elapsed }: { stageHint: string; elapsed: number }) {
  return (
    <section className="card">
      <LoadingBlock
        text={stageHint}
        hint={'已用时 ' + elapsed.toFixed(0) + ' 秒 · 单次诊断通常 20~40 秒\n流程：意图识别 → 知识检索 ∥ 数据检索 → 证据融合推理 → 待人工确认'}
      />
    </section>
  );
}
