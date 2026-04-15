// components/HashtagResults.js

import React, { useState } from 'react';

const TABS = [
  { id: 'all',      label: '⚡ All',      color: '#3b82f6' },
  { id: 'trending', label: '🔥 Trending', color: '#ef4444' },
  { id: 'broad',    label: '📈 Broad',    color: '#10b981' },
  { id: 'niche',    label: '🎯 Niche',    color: '#8b5cf6' },
];

function HashtagChip({ item, onCopy }) {
  const [copied, setCopied] = useState(false);

  const handleClick = () => {
    navigator.clipboard.writeText(item.tag);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
    if (onCopy) onCopy(item.tag);
  };

  const categoryColors = {
    trending: { bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.3)',   text: '#fca5a5' },
    broad:    { bg: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.3)',  text: '#6ee7b7' },
    niche:    { bg: 'rgba(139,92,246,0.1)',  border: 'rgba(139,92,246,0.3)',  text: '#c4b5fd' },
  };

  const colors = categoryColors[item.category] || categoryColors.broad;

  return (
    <button
      className="hashtag-chip"
      onClick={handleClick}
      title={`Score: ${item.score} · ${item.label} · Click to copy`}
      style={{
        background: colors.bg,
        borderColor: colors.border,
        color: colors.text,
      }}
    >
      <span className="chip-tag">{copied ? '✓ Copied!' : item.tag}</span>
      <span className="chip-score">{item.score}</span>
    </button>
  );
}

export default function HashtagResults({ result, activeTab, setActiveTab, displayedHashtags, platform }) {
  const [copiedAll, setCopiedAll] = useState(false);
  const [copiedTags, setCopiedTags] = useState([]);

  const handleCopyAll = () => {
    const allTags = result.hashtags.map(h => h.tag).join(' ');
    navigator.clipboard.writeText(allTags);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleCopyCategory = () => {
    const tags = displayedHashtags.map(h => h.tag).join(' ');
    navigator.clipboard.writeText(tags);
  };

  const trackCopy = (tag) => {
    setCopiedTags(prev => [...prev.slice(-4), tag]);
  };

  // Build the full hashtag string for preview
  const allTagsString = result.hashtags.slice(0, 10).map(h => h.tag).join(' ');

  return (
    <div className="results-panel">
      {/* Stats row */}
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-num">{result.total}</span>
          <span className="stat-lbl">Total</span>
        </div>
        <div className="stat-card trending-card">
          <span className="stat-num">{result.trending?.length || 0}</span>
          <span className="stat-lbl">🔥 Trending</span>
        </div>
        <div className="stat-card broad-card">
          <span className="stat-num">{result.broad?.length || 0}</span>
          <span className="stat-lbl">📈 Broad</span>
        </div>
        <div className="stat-card niche-card">
          <span className="stat-num">{result.niche?.length || 0}</span>
          <span className="stat-lbl">🎯 Niche</span>
        </div>
      </div>

      {/* Caption preview box */}
      <div className="caption-preview">
        <div className="caption-preview-header">
          <span className="caption-label">📋 Caption Preview</span>
          <button className="copy-all-btn" onClick={handleCopyAll}>
            {copiedAll ? '✓ Copied All!' : '⎘ Copy All Hashtags'}
          </button>
        </div>
        <p className="caption-text">
          {result.input_text} <span className="caption-tags">{allTagsString}…</span>
        </p>
      </div>

      {/* Category Tabs */}
      <div className="tabs-row">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            style={activeTab === tab.id ? { borderColor: tab.color, color: tab.color } : {}}
          >
            {tab.label}
            <span className="tab-count">
              {tab.id === 'all'      ? result.hashtags?.length
               : tab.id === 'trending' ? result.trending?.length
               : tab.id === 'broad'    ? result.broad?.length
               :                         result.niche?.length}
            </span>
          </button>
        ))}
        <button className="copy-cat-btn" onClick={handleCopyCategory} title="Copy this category">
          ⎘ Copy Tab
        </button>
      </div>

      {/* Hashtag chips grid */}
      <div className="chips-grid">
        {displayedHashtags.length > 0
          ? displayedHashtags.map((item, i) => (
              <HashtagChip key={i} item={item} onCopy={trackCopy} />
            ))
          : <p className="empty-msg">No hashtags in this category.</p>
        }
      </div>

      {/* Legend */}
      <div className="legend-row">
        <span className="legend-item"><span className="dot-trending" /> Trending (score ≥ 80)</span>
        <span className="legend-item"><span className="dot-broad" /> Broad (60–79)</span>
        <span className="legend-item"><span className="dot-niche" /> Niche (&lt;60)</span>
        <span className="legend-tip">💡 Click any hashtag to copy it</span>
      </div>
    </div>
  );
}