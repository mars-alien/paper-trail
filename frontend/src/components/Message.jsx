import { useEffect, useRef } from 'react'
import SourceChips from './SourceChips.jsx'
import { renderMarkdown } from '../utils/markdown.js'
import styles from './Message.module.css'

function TypingDots() {
  return (
    <div className={styles.typing}>
      <span /><span /><span />
    </div>
  )
}

export default function Message({ msg }) {
  const bodyRef = useRef(null)

  useEffect(() => {
    if (bodyRef.current && msg.role === 'ai') {
      bodyRef.current.innerHTML = renderMarkdown(msg.text)
    }
  }, [msg.text, msg.role])

  if (msg.role === 'user') {
    return (
      <div className={styles.userRow}>
        <div className={styles.userBubble}>{msg.text}</div>
      </div>
    )
  }

  return (
    <div className={styles.aiRow}>
      <div className={styles.avatar}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <line x1="10" y1="9" x2="8" y2="9"/>
        </svg>
      </div>
      <div className={styles.aiContent}>
        <div className={`${styles.aiBubble} ${msg.error ? styles.error : ''}`}>
          {msg.text === '' && msg.streaming
            ? <TypingDots />
            : <div ref={bodyRef} className={styles.mdBody} />
          }
        </div>
        {!msg.streaming && <SourceChips sources={msg.sources} />}
      </div>
    </div>
  )
}
