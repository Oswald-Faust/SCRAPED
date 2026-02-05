import { useState } from 'react'
import './index.css'

// Replace LeakData with a more flexible Record type
type LeakData = Record<string, string | null>;

interface BotButton {
  text: string;
  msg_id: number;
  url?: string;
}

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<LeakData | null>(null)
  const [buttons, setButtons] = useState<BotButton[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setData(null)
    setButtons([])

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Une erreur est survenue.')
      }

      const result = await response.json()
      setData(result.data)
      setButtons(result.buttons || [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue.')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (!data) return;
    
    // Create a text representation of the data
    const content = Object.keys(data)
      .filter(key => key !== 'raw')
      .map(key => `${key}: ${data[key]}`)
      .join('\n');
      
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `leak_result_${data['E-mail'] || 'data'}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleButtonClick = async (button: BotButton) => {
    // Check if it's a "Download" button from the bot, OR if we handle it locally
    if (button.text.toLowerCase().includes('télécharger') || button.text.toLowerCase().includes('download')) {
      handleDownload();
      return;
    }
    
    if (button.url) {
      window.open(button.url, '_blank');
      return;
    }

    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message_id: button.msg_id,
          button_text: button.text
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Erreur lors du clic.')
      }

      const result = await response.json()
      
      setData(prev => {
        if (!prev) return result.data;
        const newData = { ...prev };
        const incoming = result.data;
        
        Object.keys(incoming).forEach(key => {
          if (incoming[key] !== null && incoming[key] !== undefined && incoming[key] !== '') {
            newData[key] = incoming[key];
          }
        });
        
        return newData;
      });

      setButtons(result.buttons || [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erreur lors du clic.')
    } finally {
      setLoading(false)
    }
  }

  // Filter and sort keys for UI
  const getVisibleKeys = () => {
    if (!data) return [];
    return Object.keys(data)
      .filter(key => key !== 'raw' && data[key])
      .sort((a, b) => {
        // Boost priority fields to the top
        const priority = ['Source', 'E-mail', 'Mot de passe crypté', 'Nom', 'Prénom', 'Téléphone'];
        const aIdx = priority.indexOf(a);
        const bIdx = priority.indexOf(b);
        if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
        if (aIdx !== -1) return -1;
        if (bIdx !== -1) return 1;
        return a.localeCompare(b);
      });
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
          {loading ? '...' : 'Analyser'}
        </button>
      </form>

      {loading && (
        <div className="loading-container">
          <span className="loader"></span>
          <p style={{ color: 'var(--text-secondary)' }}>Cherchons les données...</p>
        </div>
      )}

      {error && (
        <div className="glass" style={{ padding: '20px', color: '#ff453a', border: '1px solid rgba(255, 69, 58, 0.2)', maxWidth: '600px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {buttons.length > 0 && (
        <div className="glass" style={{ padding: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '30px', maxWidth: '1000px', justifyContent: 'center' }}>
          {buttons.map((btn, idx) => (
            <button 
              key={idx} 
              className="search-button" 
              style={{ position: 'relative', right: 'unset', top: 'unset', bottom: 'unset', padding: '10px 20px' }}
              onClick={() => handleButtonClick(btn)}
              disabled={loading}
            >
              {btn.text}
            </button>
          ))}
        </div>
      )}

      {data && (
        <div className={`results-grid visible`}>
          {getVisibleKeys().map(key => (
            <div key={key} className="result-card glass">
              <div className="card-label">{key}</div>
              <div 
                className="card-value" 
                style={{ 
                  color: key.toLowerCase().includes('pass') ? '#ff375f' : key === 'Source' ? 'var(--accent-color)' : 'white',
                  fontFamily: key.toLowerCase().includes('pass') ? 'monospace' : 'inherit'
                }}
              >
                {data[key]}
              </div>
            </div>
          ))}
        </div>
      )}

      {data && data.raw && getVisibleKeys().length === 0 && (
        <div className="glass" style={{ marginTop: '40px', padding: '20px', maxWidth: '800px', width: '100%' }}>
           <div className="card-label" style={{ marginBottom: '10px' }}>Log Brut</div>
           <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{data.raw}</pre>
        </div>
      )}
    </>
  )
}

export default App
