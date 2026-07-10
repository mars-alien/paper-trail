import { useState, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar.jsx'
import Message from './components/Message.jsx'
import InputBar from './components/InputBar.jsx'
import Welcome from './components/Welcome.jsx'
import { useChat } from './hooks/useChat.js'
import { fetchStarters, fetchArticles, ingestUrls, deleteArticle } from './utils/api.js'
import styles from './App.module.css'

const MOBILE_BP = 880

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < MOBILE_BP)
  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BP - 1}px)`)
    const handler = e => setIsMobile(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return isMobile
}

export default function App() {
  const [starters, setStarters]       = useState([])
  const [articles, setArticles]       = useState([])
  const [ingesting, setIngesting]     = useState(false)
  const isMobile                      = useIsMobile()
  const [mobileOpen, setMobileOpen]   = useState(false)   // mobile drawer
  const [collapsed, setCollapsed]     = useState(false)   // desktop rail
  const { messages, loading, sendMessage } = useChat()
  const bottomRef = useRef(null)

  // close mobile drawer when switching to desktop
  useEffect(() => { if (!isMobile) setMobileOpen(false) }, [isMobile])

  useEffect(() => {
    fetchStarters().then(setStarters).catch(() => {})
    fetchArticles().then(setArticles).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleIngest(urls) {
    setIngesting(true)
    try {
      const { results } = await ingestUrls(urls)
      if (results.some(r => r.status === 'ok')) {
        const fresh = await fetchArticles()
        setArticles(fresh)
      }
      return results
    } finally {
      setIngesting(false)
    }
  }

  async function handleDelete(doc_id) {
    await deleteArticle(doc_id)
    setArticles(prev => prev.filter(a => a.doc_id !== doc_id))
  }

  function handleSend(text) {
    sendMessage(text, { doc_ids: [] })
  }

  function handleToggleSidebar() {
    if (isMobile) setMobileOpen(p => !p)
    else setCollapsed(p => !p)
  }

  // On mobile: sidebar renders only when drawer is open
  // On desktop: sidebar always renders (collapsed = rail mode)
  const sidebarVisible = isMobile ? mobileOpen : true

  return (
    <div className={styles.app} data-theme="b">
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <button className={styles.menuBtn} onClick={handleToggleSidebar} aria-label="Toggle sidebar">
            <span className={styles.hamBar} />
            <span className={styles.hamBar} />
            <span className={styles.hamBar} />
          </button>

          <div>
            <div className={styles.brandName}>PaperTrail</div>
            <div className={styles.brandSub}>Add articles · Ask questions · Get cited answers</div>
          </div>
        </div>

      </header>

      <div className={styles.body}>
        {/* Mobile backdrop */}
        {isMobile && mobileOpen && (
          <div className={styles.overlay} onClick={() => setMobileOpen(false)} />
        )}

        {sidebarVisible && (
          <Sidebar
            open={true}
            collapsed={!isMobile && collapsed}
            onExpand={() => setCollapsed(false)}
            articles={articles}
            ingesting={ingesting}
            onIngest={handleIngest}
            onDelete={handleDelete}
          />
        )}

        <main className={styles.main}>
          {messages.length === 0 ? (
            <Welcome starters={starters} articleCount={articles.length} onSelect={handleSend} />
          ) : (
            <div className={styles.messages}>
              {messages.map(msg => <Message key={msg.id} msg={msg} />)}
              <div ref={bottomRef} />
            </div>
          )}
          <InputBar onSend={handleSend} disabled={loading} />
        </main>
      </div>
    </div>
  )
}
