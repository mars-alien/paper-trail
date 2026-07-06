import styles from './SourceChips.module.css'

const COLORS = ['#4f8ef7','#10b981','#f59e0b','#a855f7','#ef4444','#06b6d4','#f97316','#84cc16']

function domainColor(domain) {
  let hash = 0
  for (let i = 0; i < domain.length; i++) hash = domain.charCodeAt(i) + ((hash << 5) - hash)
  return COLORS[Math.abs(hash) % COLORS.length]
}

export default function SourceChips({ sources }) {
  if (!sources || sources.length === 0) return null

  const seen = new Set()
  const unique = sources.filter(s => {
    if (seen.has(s.doc_id)) return false
    seen.add(s.doc_id)
    return true
  })

  return (
    <div className={styles.container}>
      <span className={styles.label}>Sources</span>
      <div className={styles.chips}>
        {unique.map((s, i) => (
          <a
            key={i}
            className={styles.chip}
            href={s.url}
            target="_blank"
            rel="noreferrer"
            title={s.title}
          >
            <span className={styles.dot} style={{ background: domainColor(s.source) }} />
            <div className={styles.meta}>
              <span className={styles.source}>{s.source}</span>
              <span className={styles.title}>
                {s.title.length > 50 ? s.title.slice(0, 50) + '...' : s.title}
              </span>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
