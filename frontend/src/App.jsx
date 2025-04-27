import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function AccordionItem({ title, children, isOpen, onToggle }) {
  return (
    <div className="accordion-item">
      <div 
        className={`accordion-header ${isOpen ? 'open' : ''}`} 
        onClick={onToggle}
      >
        <h3>{title}</h3>
        <span className="accordion-icon">{isOpen ? '▼' : '▶'}</span>
      </div>
      {isOpen && (
        <div className="accordion-content">
          {children}
        </div>
      )}
    </div>
  );
}

function App() {
  const [url, setUrl] = useState("");
  const [referenceUrl, setReferenceUrl] = useState("");
  const [maxPatchNotes, setMaxPatchNotes] = useState(3);
  const [loading, setLoading] = useState(false);
  const [loadingDots, setLoadingDots] = useState(0);
  const [error, setError] = useState(null);
  const [summaries, setSummaries] = useState([]);
  const [openAccordions, setOpenAccordions] = useState({});

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
    setOpenAccordions({});

    try {
      const response = await fetch("http://localhost:5000/api/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          url,
          reference_url: referenceUrl || undefined,
          max_patch_notes: maxPatchNotes
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch summaries");
      }

      setSummaries(data.patch_notes);
      
      // Set the first accordion to be open by default
      if (data.patch_notes.length > 0) {
        setOpenAccordions({ 0: true });
      }
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

  const toggleAccordion = (index) => {
    setOpenAccordions(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const formatTitle = (summary) => {
    if (summary.title) {
      let title = summary.title;
      if (summary.date) {
        title += ` (${summary.date})`;
      }
      if (summary.version) {
        title += ` - ${summary.version}`;
      }
      return title;
    }
    return "Patch Notes Summary";
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

          <div className="form-group">
            <div className="input-with-tooltip">
              <select
                id="max-patch-notes"
                value={maxPatchNotes}
                onChange={(e) => setMaxPatchNotes(parseInt(e.target.value))}
                className="url-input"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                  <option key={num} value={num}>
                    {num} {num === 1 ? 'Patch Note' : 'Patch Notes'}
                  </option>
                ))}
              </select>
              <div className="tooltip-icon">?
                <span className="tooltip-text">
                  Select how many patch notes you want to summarize.
                  More patch notes will take longer to process.
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
              <AccordionItem 
                key={index}
                title={formatTitle(summary)}
                isOpen={openAccordions[index] || false}
                onToggle={() => toggleAccordion(index)}
              >
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
              </AccordionItem>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
