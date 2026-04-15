// components/InputPanel.js

import React from 'react';

const COUNT_OPTIONS = [10, 15, 20, 30, 50];

export default function InputPanel({
  text, setText, count, setCount,
  onGenerate, onReset, loading, hasResult
}) {
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const canGenerate = text.trim().length >= 3 && !loading;

  return (
    <div className="input-panel">
      <div className="input-panel-header">
        <h2 className="panel-title">✍ Describe Your Content</h2>
        <p className="panel-sub">Enter your post caption, topic, or description</p>
      </div>

      {/* Textarea */}
      <textarea
        className="main-textarea"
        placeholder={
          "e.g. Just finished building an AI app using Python and machine learning...\n\nor: My travel adventure in Bali with stunning sunsets and beautiful beaches"
        }
        value={text}
        onChange={e => setText(e.target.value)}
        disabled={loading}
        rows={5}
      />

      <div className="input-meta">
        <span className="word-count">{wordCount} words · {text.length} chars</span>

        {/* Count selector */}
        <div className="count-selector">
          <span className="count-label">Hashtags:</span>
          {COUNT_OPTIONS.map(n => (
            <button
              key={n}
              className={`count-btn ${count === n ? 'active' : ''}`}
              onClick={() => setCount(n)}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {/* Action buttons */}
      <div className="input-actions">
        {hasResult && (
          <button className="btn btn-ghost" onClick={onReset}>
            ← New
          </button>
        )}
        <button
          className="btn btn-primary"
          onClick={onGenerate}
          disabled={!canGenerate}
        >
          {loading
            ? <><span className="spinner" /> Generating…</>
            : '# Generate Hashtags'
          }
        </button>
      </div>
    </div>
  );
}