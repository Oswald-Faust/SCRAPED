import { useState } from 'react'
import './index.css'

interface LeakData {
  email: string | null;
  phone: string | null;
  password: string | null;
  fullname: string | null;
  source: string | null;
  raw?: string;
}

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<LeakData | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setData(null)

    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Une erreur est survenue lors de la recherche.')
      }

      const result = await response.json()
      setData(result.data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <h1>Scraped Cloud</h1>
      <p className="subtitle">
        L'intelligence en temps réel pour la sécurité de vos données. 
        Recherchez parmi des millions de fuites via notre Smart Proxying Engine.
      </p>

      <form className="search-container" onSubmit={handleSearch}>
        <input 
          type="text" 
          className="search-input" 
          placeholder="Entrez un email, un nom ou un pseudo..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="search-button" disabled={loading}>
          {loading ? 'Recherche...' : 'Analyser'}
        </button>
      </form>

      {loading && (
        <div className="loading-container">
          <span className="loader"></span>
          <p style={{ color: 'var(--text-secondary)' }}>Connexion au bot Telegram et extraction...</p>
        </div>
      )}

      {error && (
        <div className="glass" style={{ padding: '20px', color: '#ff453a', border: '1px solid rgba(255, 69, 58, 0.2)', maxWidth: '600px' }}>
          {error}
        </div>
      )}

      {data && (
        <div className={`results-grid ${data ? 'visible' : ''}`}>
          <div className="result-card glass">
            <div>
              <div className="card-label">Email Principal</div>
              <div className="card-value">{data.email || 'N/A'}</div>
            </div>
          </div>
          
          <div className="result-card glass">
            <div>
              <div className="card-label">Téléphone</div>
              <div className="card-value">{data.phone || 'N/A'}</div>
            </div>
          </div>

          <div className="result-card glass">
            <div>
              <div className="card-label">Mot de Passe</div>
              <div className="card-value" style={{ fontFamily: 'monospace', fontSize: '1rem' }}>
                {data.password || 'Non trouvé'}
              </div>
            </div>
          </div>

          <div className="result-card glass">
            <div>
              <div className="card-label">Identité / Nom</div>
              <div className="card-value">{data.fullname || 'Anonyme'}</div>
            </div>
          </div>

          <div className="result-card glass" style={{ gridColumn: 'span 1' }}>
            <div>
              <div className="card-label">Source de la Fuite</div>
              <div className="card-value" style={{ color: 'var(--accent-color)' }}>{data.source || 'Inconnue'}</div>
            </div>
          </div>
        </div>
      )}

      {data && data.raw && !data.email && !data.phone && (
        <div className="glass" style={{ marginTop: '40px', padding: '20px', maxWidth: '800px', width: '100%' }}>
           <div className="card-label" style={{ marginBottom: '10px' }}>Texte Brut (Format non reconnu)</div>
           <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{data.raw}</pre>
        </div>
      )}
    </>
  )
}

export default App
