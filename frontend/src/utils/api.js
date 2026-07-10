const BASE = import.meta.env.VITE_API_URL || '/api'

export async function fetchStarters() {
  const res = await fetch(`${BASE}/starters`)
  if (!res.ok) throw new Error('failed')
  return res.json()
}

export async function fetchArticles() {
  const res = await fetch(`${BASE}/articles`)
  if (!res.ok) throw new Error('failed')
  return res.json()
}

export async function ingestUrls(urls) {
  const res = await fetch(`${BASE}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ urls }),
  })
  if (!res.ok) throw new Error(`Server error ${res.status}`)
  return res.json()
}

export async function deleteArticle(doc_id) {
  const res = await fetch(`${BASE}/articles/${doc_id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('failed')
  return res.json()
}

export async function streamQuery({ question, history, doc_ids }, onToken, onDone, onError) {
  try {
    const res = await fetch(`${BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history, doc_ids: doc_ids || [] }),
    })
    if (!res.ok) {
      onError(`Server error ${res.status}. Is the backend running?`)
      return
    }
    const reader  = res.body.getReader()
    const decoder = new TextDecoder()
    let sources   = []
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      for (const line of decoder.decode(value).split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const ev = JSON.parse(line.slice(6))
          if (ev.type === 'token') onToken(ev.text)
          else if (ev.type === 'done') sources = ev.sources || []
        } catch (_) {}
      }
    }
    onDone(sources)
  } catch (err) {
    onError(err.message)
  }
}
