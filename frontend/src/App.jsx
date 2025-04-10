import { useState } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState('')
  const [cutoffDate, setCutoffDate] = useState('')
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSummary('')

    try {
      const response = await fetch('http://localhost:5000/api/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          url,
          cutoff_date: cutoffDate || undefined,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Server error: ${response.status}`)
      }

      const data = await response.json()
      setSummary(data.summary)
    } catch (err) {
      console.error('Error:', err)
      setError(err.message || 'An error occurred while fetching the summary')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Product Update Summarizer</h1>
      <p className="description">
        Enter a product update or patch notes URL to get a concise summary of the changes.
      </p>

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label htmlFor="url">Update URL</label>
          <input
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/product-updates"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="cutoff-date">Summarize updates since (optional)</label>
          <input
            type="date"
            id="cutoff-date"
            value={cutoffDate}
            onChange={(e) => setCutoffDate(e.target.value)}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Summarizing...' : 'Summarize Updates'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {summary && (
        <div className="summary-container">
          <h2>Summary</h2>
          <div className="summary">{summary}</div>
        </div>
      )}
    </div>
  )
}

export default App
