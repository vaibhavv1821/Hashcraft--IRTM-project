// components/TrendingPanel.js

import React, { useState } from 'react';

export default function TrendingPanel({ trending, platform, platforms, onPlatformChange }) {
  const [copied, setCopied] = useState('');

  const handleCopy = (tag) => {
    navigator.clipboard.writeText(tag);
    setCopied(tag);
    setTimeout(() => setCopied(''), 1500);
  };

  const currentPlatform = platforms.find(p => p.id === platform);

  return (
    <div className="trending-panel">
      <div className="trending-header">
        <h3 className="trending-title">
          🔥 Trending Now
        </h3>
        <p className="trending-sub">
          {currentPlatform?.icon} {currentPlatform?.label}
        </p>
      </div>

      {/* Mini platform switcher */}
      <div className="mini-platforms">
        {platforms.map(p => (
          <button
            key={p.id}
            className={`mini-platform-btn ${platform === p.id ? 'active' : ''}`}
            onClick={() => onPlatformChange(p.id)}
            title={p.label}
          >
            {p.icon}
          </button>
        ))}
      </div>

      {/* Trending list */}
      <div className="trending-list">
        {trending.length === 0 && (
          <p className="trending-empty">Loading trending tags…</p>
        )}
        {trending.map((item, i) => (
          <div key={i} className="trending-item">
            <div className="trending-rank">#{i + 1}</div>
            <div className="trending-info">
              <span className="trending-tag">{item.tag}</span>
              <div className="trending-bar-wrap">
                <div
                  className="trending-bar"
                  style={{ width: `${item.score}%` }}
                />
              </div>
            </div>
            <div className="trending-right">
              <span className="trending-score">{item.score}</span>
              <button
                className="trending-copy-btn"
                onClick={() => handleCopy(item.tag)}
              >
                {copied === item.tag ? '✓' : '⎘'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Info card */}
      <div className="info-card">
        <h4>💡 Pro Tips</h4>
        <ul className="tips-list">
          <li>Mix trending + niche tags for best reach</li>
          <li>Instagram allows up to 30 hashtags</li>
          <li>LinkedIn: 3–5 hashtags work best</li>
          <li>Twitter/X: 1–2 hashtags recommended</li>
          <li>YouTube: use in description</li>
          <li>GitHub: add to repo topics</li>
        </ul>
      </div>
    </div>
  );
}