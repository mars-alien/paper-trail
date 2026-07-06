import { useState, useCallback, useRef } from 'react'
import { streamQuery } from '../utils/api.js'

export function useChat() {
  const [messages, setMessages]   = useState([])
  const [loading, setLoading]     = useState(false)
  const historyRef = useRef([])

  const sendMessage = useCallback(async (question, { doc_ids = [] } = {}) => {
    if (!question.trim() || loading) return

    const userMsg = { id: Date.now(),     role: 'user', text: question }
    const aiId   = Date.now() + 1
    const aiMsg  = { id: aiId, role: 'ai', text: '', sources: [], streaming: true }

    setMessages(prev => [...prev, userMsg, aiMsg])
    setLoading(true)

    await streamQuery(
      { question, history: historyRef.current, doc_ids },
      token => setMessages(prev =>
        prev.map(m => m.id === aiId ? { ...m, text: m.text + token } : m)
      ),
      sources => {
        setMessages(prev =>
          prev.map(m => m.id === aiId ? { ...m, sources, streaming: false } : m)
        )
        historyRef.current = [
          ...historyRef.current,
          { role: 'user', content: question },
        ].slice(-20)
        setLoading(false)
      },
      errMsg => {
        setMessages(prev =>
          prev.map(m => m.id === aiId
            ? { ...m, text: `Error: ${errMsg}`, error: true, streaming: false }
            : m
          )
        )
        setLoading(false)
      }
    )
  }, [loading])

  const clearChat = useCallback(() => {
    setMessages([])
    historyRef.current = []
  }, [])

  return { messages, loading, sendMessage, clearChat }
}
