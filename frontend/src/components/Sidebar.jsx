import { useState, useRef } from 'react'
import styles from './Sidebar.module.css'

function NewsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>
      <path d="M18 14h-8M15 18h-5M10 6h8v4h-8z"/>
    </svg>
  )
}

function PlusIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  )
}

export default function Sidebar({ open, collapsed, onExpand, articles, ingesting, onIngest, onDelete }) {
  const [urlInput, setUrlInput]       = useState('')
  const [results, setResults]         = useState([])
  const [showResults, setShowResults] = useState(false)
  const textareaRef = useRef(null)

  async function handleAdd() {
    const urls = urlInput.split('\n').map(u => u.trim()).filter(Boolean)
    if (!urls.length) return
    setResults([])
    setShowResults(false)
    const res = await onIngest(urls)
    setResults(res)
    setShowResults(true)
    setUrlInput('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && e.ctrlKey) handleAdd()
  }

  if (!open) return null

  // Rail (icon-only) mode on desktop when collapsed
  if (collapsed) {
    return (
      <aside className={styles.rail} onClick={onExpand} title="Expand sidebar">
        <div className={styles.railIcon} title="Articles">
          <NewsIcon />
          {articles.length > 0 && (
            <span className={styles.railBadge}>{articles.length}</span>
          )}
        </div>
        <div className={styles.railIcon} title="Add article">
          <PlusIcon />
        </div>
      </aside>
    )
  }

  return (
    <aside className={styles.sidebar}>
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Add Articles</h2>
        <textarea
          ref={textareaRef}
          className={styles.urlInput}
          placeholder={'Paste one or more news URLs\n(one per line)'}
          value={urlInput}
          onChange={e => setUrlInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={4}
          disabled={ingesting}
        />
        <button
          className={`${styles.addBtn} ${ingesting ? styles.loading : ''}`}
          onClick={handleAdd}
          disabled={ingesting || !urlInput.trim()}
        >
          {ingesting ? 'Ingesting...' : 'Add Articles'}
        </button>
        <p className={styles.hint}>Ctrl+Enter to add</p>

        {showResults && results.length > 0 && (
          <div className={styles.results}>
            {results.map((r, i) => (
              <div key={i} className={`${styles.resultRow} ${styles[r.status]}`}>
                <span className={styles.resultIcon}>
                  {r.status === 'ok' ? '✓' : r.status === 'skipped' ? '↩' : '✕'}
                </span>
                <span className={styles.resultText}>
                  {r.status === 'ok'
                    ? `${r.title?.slice(0, 40) || r.url} (${r.chunks} chunks)`
                    : r.status === 'skipped'
                    ? 'Already ingested'
                    : r.error || 'Failed'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>
          Articles
          <span className={styles.count}>{articles.length}</span>
        </h2>
        {articles.length === 0 ? (
          <p className={styles.empty}>No articles yet. Paste URLs above to get started.</p>
        ) : (
          <div className={styles.articleList}>
            {articles.map(a => (
              <div key={a.doc_id} className={styles.articleCard}>
                <div className={styles.articleMeta}>
                  <span className={styles.domain}>{a.source_domain}</span>
                  {a.published_date && <span className={styles.date}>{a.published_date}</span>}
                </div>
                <a
                  className={styles.articleTitle}
                  href={a.url}
                  target="_blank"
                  rel="noreferrer"
                  title={a.title}
                >
                  {a.title.length > 65 ? a.title.slice(0, 65) + '…' : a.title}
                </a>
                <div className={styles.articleFooter}>
                  <span className={styles.chunks}>{a.chunks_count} chunks</span>
                  <button
                    className={styles.deleteBtn}
                    onClick={() => onDelete(a.doc_id)}
                    title="Remove article"
                  >✕</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}
