import styles from './Welcome.module.css'

function OrbitHeroIcon() {
  return (
    <div className={styles.heroIconWrap}>
      <svg width="56" height="56" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="28" cy="28" r="13" fill="currentColor" opacity="0.15"/>
        <circle cx="28" cy="28" r="8" fill="currentColor" opacity="0.85"/>
        <ellipse cx="28" cy="28" rx="24" ry="9" fill="none" stroke="currentColor" strokeWidth="2" opacity="0.6" transform="rotate(-28 28 28)"/>
        <circle cx="46" cy="18" r="3.5" fill="currentColor"/>
      </svg>
    </div>
  )
}

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
