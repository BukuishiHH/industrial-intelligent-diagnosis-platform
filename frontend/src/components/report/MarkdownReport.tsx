import { useMemo } from 'react';
import { renderMarkdown } from '../../utils/markdown';

/** 报告渲染：Markdown -> 已转义 HTML（内容按不可信来源处理） */
export function MarkdownReport({ content }: { content: string }) {
  const html = useMemo(() => renderMarkdown(content), [content]);
  return <article className="report" dangerouslySetInnerHTML={{ __html: html }} />;
}
