// frontend/src/components/TrendingPanel.js

import React, { useState } from 'react';

const PLATFORMS = [
  { id: 'all',       icon: '🌐' },
  { id: 'instagram', icon: '📸' },
  { id: 'twitter',   icon: '𝕏'  },
  { id: 'linkedin',  icon: '💼' },
  { id: 'youtube',   icon: '▶'  },
  { id: 'github',    icon: '🐙' },
];

const TIPS = {
  all:       ['Mix trending and niche tags', 'Update hashtags regularly', 'Research competitor tags'],
  instagram: ['Use 20-30 hashtags per post', 'Put tags in first comment', 'Avoid banned hashtags'],
  twitter:   ['Use only 1-3 hashtags', 'Place at end of tweet', 'Capitalize: #MondayMotivation'],
  linkedin:  ['3-5 hashtags is ideal', 'Use professional tone', 'Follow your own hashtags'],
  youtube:   ['Add in video description', 'First 3 appear above title', 'Use 3-5 relevant tags'],
  github:    ['Add as repository Topics', 'Use lowercase with hyphens', 'Max 20 topics per repo'],
};

export default function TrendingPanel({ trending, platform, onPlatformChange, isRealtime }) {
  const [copied, setCopied] = useState('');

  const copy = (tag) => {
    navigator.clipboard.writeText(tag);
    setCopied(tag);
    setTimeout(() => setCopied(''), 1500);
  };

  const tips = TIPS[platform] || TIPS.all;

  return (
    <div className="trending-panel">

      {/* Header */}
      <div className="tp-header">
        <h3 className="tp-title">🔥 Trending Now</h3>
        <span className={`tp-source ${isRealtime ? 'live' : 'curated'}`}>
          {isRealtime ? '🟢 Live' : '⚪ Curated'}
        </span>
      </div>

      {/* Platform switcher */}
      <div className="tp-platforms">
        {PLATFORMS.map(p => (
          <button
            key={p.id}
            className={`tp-plat-btn ${platform === p.id ? 'active' : ''}`}
            onClick={() => onPlatformChange(p.id)}
            title={p.id}
          >
            {p.icon}
          </button>
        ))}
      </div>

      {/* Trending list */}
      <div className="tp-list">
        {trending.length === 0 && (
          <p className="tp-empty">Loading trends…</p>
        )}
        {trending.slice(0, 15).map((item, i) => {
          // Fix: safely extract score as a plain number
          const score = typeof item.score === 'number'
            ? item.score
            : parseInt(String(item.score), 10) || 0;

          return (
            <div key={i} className="tp-item">
              <span className="tp-rank">#{i + 1}</span>
              <div className="tp-info">
                <span className="tp-tag">{item.tag}</span>
                <div className="tp-bar-wrap">
                  <div className="tp-bar" style={{ width: `${score}%` }} />
                </div>
              </div>
              <div className="tp-right">
                <span className="tp-score">{score}</span>
                <button className="tp-copy" onClick={() => copy(item.tag)}>
                  {copied === item.tag ? '✓' : '⎘'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Tips */}
      <div className="tips-card">
        <h4 className="tips-title">
          💡 {platform.charAt(0).toUpperCase() + platform.slice(1)} Tips
        </h4>
        <ul className="tips-list">
          {tips.map((tip, i) => (
            <li key={i} className="tips-item">{tip}</li>
          ))}
        </ul>
      </div>

    </div>
  );
}