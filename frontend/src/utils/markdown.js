// Simple markdown -> HTML converter for LLM responses
export function renderMarkdown(text) {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Code blocks
  html = html.replace(/```[\w]*\n?([\s\S]*?)```/g, '<pre><code>$1</code></pre>')

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Italic
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // Numbered list items
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')

  // Bullet list items
  html = html.replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>')

  // Wrap consecutive <li> in <ul>
  html = html.replace(/(<li>[\s\S]*?<\/li>)(\s*(?!<li>))/g, '<ul>$1</ul>$2')

  // Paragraphs (double newline)
  html = html.replace(/\n\n+/g, '</p><p>')

  // Single newlines
  html = html.replace(/\n/g, '<br/>')

  return `<p>${html}</p>`
}
