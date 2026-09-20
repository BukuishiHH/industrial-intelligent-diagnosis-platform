/**
 * 轻量 Markdown 渲染器（零依赖）。
 *
 * 针对本平台报告模板的结构（标题/表格/列表/引用/分隔线/加粗/行内代码）实现，
 * **所有文本先做 HTML 转义再拼接**，因此不存在 XSS 风险（报告内容虽由本方生成，
 * 但仍按不可信内容处理）。
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function inline(text: string): string {
  let html = escapeHtml(text);
  // 行内代码：\x60 即反引号
  html = html.replace(/\x60([^\x60]+)\x60/g, '<code>$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  return html;
}

function splitRow(line: string): string[] {
  return line.replace(/^\|/, '').replace(/\|$/, '').split('|').map((cell) => cell.trim());
}

export function renderMarkdown(markdown: string): string {
  const lines = (markdown ?? '').replace(/\r\n/g, '\n').split('\n');
  const out: string[] = [];
  let listType: 'ul' | 'ol' | null = null;
  let inTable = false;
  let tableHeadDone = false;

  const closeList = () => {
    if (listType) {
      out.push('</' + listType + '>');
      listType = null;
    }
  };
  const closeTable = () => {
    if (inTable) {
      out.push('</tbody></table>');
      inTable = false;
      tableHeadDone = false;
    }
  };

  for (let i = 0; i < lines.length; i += 1) {
    const raw = lines[i];
    const line = raw.trim();

    if (!line) {
      closeList();
      closeTable();
      continue;
    }
    if (/^-{3,}$/.test(line)) {
      closeList();
      closeTable();
      out.push('<hr />');
      continue;
    }
    if (line.startsWith('|')) {
      closeList();
      const cells = splitRow(line);
      const next = (lines[i + 1] ?? '').trim();
      const isSeparator = /^\|[\s:|-]+\|?$/.test(next);
      if (!inTable) {
        out.push('<table><thead><tr>');
        cells.forEach((cell) => out.push('<th>' + inline(cell) + '</th>'));
        out.push('</tr></thead><tbody>');
        inTable = true;
        tableHeadDone = false;
        if (isSeparator) i += 1;
        continue;
      }
      if (isSeparator) {
        i += 1;
        continue;
      }
      if (!tableHeadDone) tableHeadDone = true;
      out.push('<tr>');
      cells.forEach((cell) => out.push('<td>' + inline(cell) + '</td>'));
      out.push('</tr>');
      continue;
    }
    closeTable();

    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (heading) {
      closeList();
      const level = heading[1].length;
      out.push('<h' + level + '>' + inline(heading[2]) + '</h' + level + '>');
      continue;
    }
    if (line.startsWith('>')) {
      closeList();
      out.push('<blockquote>' + inline(line.replace(/^>\s?/, '')) + '</blockquote>');
      continue;
    }
    const ordered = /^(\d+)\.\s+(.*)$/.exec(line);
    if (ordered) {
      if (listType !== 'ol') {
        closeList();
        out.push('<ol>');
        listType = 'ol';
      }
      out.push('<li>' + inline(ordered[2]) + '</li>');
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      if (listType !== 'ul') {
        closeList();
        out.push('<ul>');
        listType = 'ul';
      }
      out.push('<li>' + inline(line.replace(/^[-*]\s+/, '')) + '</li>');
      continue;
    }
    closeList();
    out.push('<p>' + inline(line) + '</p>');
  }
  closeList();
  closeTable();
  return out.join('\n');
}
