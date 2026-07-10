import styles from './Welcome.module.css'

export default function Welcome({ starters, articleCount, onSelect }) {
  return (
    <div className={styles.welcome}>
<div className={styles.copy}>
        <h2>PaperTrail</h2>
        {articleCount === 0 ? (
          <p>Paste news article URLs in the left panel to get started.<br/>Then ask any question about those articles.</p>
        ) : (
          <p>You have <strong>{articleCount}</strong> article{articleCount !== 1 ? 's' : ''} ingested.<br/>Ask a question below or pick a starter.</p>
        )}
      </div>
      {articleCount > 0 && starters.length > 0 && (
        <div className={styles.grid}>
          {starters.slice(0, 6).map((q, i) => (
            <button key={i} className={styles.card} onClick={() => onSelect(q)}>
              {q}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
