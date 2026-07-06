import { useRef, useEffect } from 'react'
import styles from './InputBar.module.css'

export default function InputBar({ onSend, disabled }) {
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!disabled) textareaRef.current?.focus()
  }, [disabled])

  function handleInput() {
    const el = textareaRef.current
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    const val = textareaRef.current.value.trim()
    if (!val || disabled) return
    onSend(val)
    textareaRef.current.value = ''
    textareaRef.current.style.height = 'auto'
  }

  return (
    <div className={styles.bar}>
      <div className={styles.inputWrap}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Ask a question about your articles..."
          rows={1}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <button
          className={`${styles.sendBtn} ${disabled ? styles.disabled : ''}`}
          onClick={submit}
          disabled={disabled}
          title="Send (Enter)"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
      <p className={styles.hint}>Press Enter to send · Shift+Enter for new line</p>
    </div>
  )
}
