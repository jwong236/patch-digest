import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [referenceUrl, setReferenceUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingDots, setLoadingDots] = useState(0);
  const [error, setError] = useState(null);
  const [summaries, setSummaries] = useState([]);

  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(() => {
        setLoadingDots((prev) => (prev + 1) % 4);
      }, 500);
    } else {
      setLoadingDots(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSummaries([]);

    try {
      const response = await fetch("http://localhost:5000/api/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          url,
          reference_url: referenceUrl || undefined
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch summaries");
      }

      setSummaries(data.patch_notes);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const processMarkdown = (text) => {
    if (!text) return "";
    
    const lines = text.split('\n');
    const processedLines = [];
    
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i];
      
      if (line.trim().startsWith('*')) {
        const leadingSpaces = line.match(/^\s*/)[0].length;
        const indentLevel = Math.floor(leadingSpaces / 4);
        
        line = ' '.repeat(indentLevel * 4) + line.trim();
      }
      
      processedLines.push(line);
    }
    
    return processedLines.join('\n');
  };

  return (
    <div className="app-container">
      <div className="content-container">
        <h1>Patch Digest</h1>
        <p className="description">
          Enter a patch notes catalogue URL to get AI-generated summaries of recent updates.
        </p>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <div className="input-with-tooltip">
              <input
                type="url"
                id="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Patch notes catalogue URL"
                required
                className="url-input"
              />
              <div className="tooltip-icon">?
                <span className="tooltip-text">
                  A patch notes catalogue is a webpage that contains links to multiple patch notes.
                  Examples: League of Legends updates page, game news sections, etc.
                </span>
              </div>
            </div>
          </div>

          <div className="form-group">
            <div className="input-with-tooltip">
              <input
                type="url"
                id="reference-url"
                value={referenceUrl}
                onChange={(e) => setReferenceUrl(e.target.value)}
                placeholder="Reference patch note URL (optional)"
                className="url-input"
              />
              <div className="tooltip-icon">?
                <span className="tooltip-text">
                  Providing a specific patch note URL helps identify similar links in the catalogue.
                  This can improve accuracy when the catalogue structure is complex.
                </span>
              </div>
            </div>
          </div>

          <button type="submit" disabled={loading} className="submit-button">
            {loading ? `Summarizing${".".repeat(loadingDots)}` : "Summarize Updates"}
          </button>
        </form>

        {error && <div className="error-message">{error}</div>}

        {summaries.length > 0 && (
          <div className="summaries-container">
            {summaries.map((summary, index) => (
              <div key={index} className="summary-card">
                <h2>Patch Notes Summary</h2>
                <div className="summary-content">
                  <ReactMarkdown>
                    {processMarkdown(summary.summary)}
                  </ReactMarkdown>
                </div>
                <div className="summary-footer">
                  <a
                    href={summary.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link"
                  >
                    View Original
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
