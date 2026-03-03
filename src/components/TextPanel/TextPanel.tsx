import { Panel } from '../../types';
import './TextPanel.css';

interface TextPanelProps {
  panel: Panel;
  data: unknown[];
  width: number;
  height: number;
}

function simpleMarkdown(text: string): string {
  return text
    .replace(/^### (.*$)/gm, '<h4>$1</h4>')
    .replace(/^## (.*$)/gm, '<h3>$1</h3>')
    .replace(/^# (.*$)/gm, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
}

export function TextPanel({ panel }: TextPanelProps) {
  const content = panel.options.content || '';
  const mode = panel.options.mode || 'markdown';

  if (mode === 'code') {
    return (
      <div className="text-panel">
        <pre className="text-code"><code>{content}</code></pre>
      </div>
    );
  }

  if (mode === 'html') {
    return (
      <div className="text-panel">
        <div className="text-html" dangerouslySetInnerHTML={{ __html: content }} />
      </div>
    );
  }

  // Markdown mode
  return (
    <div className="text-panel">
      <div
        className="text-markdown"
        dangerouslySetInnerHTML={{ __html: simpleMarkdown(content) }}
      />
    </div>
  );
}
