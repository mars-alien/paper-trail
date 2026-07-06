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
      <div className={styles.avatar}>O</div>
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
