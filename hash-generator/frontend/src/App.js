// App.js — TagCraft: Automatic Hashtag Generator

import React, { useState, useEffect } from 'react';
import InputPanel from './components/InputPanel';
import HashtagResults from './components/HashtagResults';
import TrendingPanel from './components/TrendingPanel';
import { generateHashtags, getTrending, checkHealth } from './services/api';
import './App.css';

const PLATFORMS = [
  { id: 'all',       label: 'All',       icon: '🌐' },
  { id: 'instagram', label: 'Instagram', icon: '📸' },
  { id: 'twitter',   label: 'Twitter/X', icon: '𝕏'  },
  { id: 'linkedin',  label: 'LinkedIn',  icon: '💼' },
  { id: 'youtube',   label: 'YouTube',   icon: '▶'  },
  { id: 'github',    label: 'GitHub',    icon: '🐙' },
];

export default function App() {
  const [text, setText] = useState('');
  const [platform, setPlatform] = useState('all');
  const [count, setCount] = useState(20);
  const [result, setResult] = useState(null);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [apiOnline, setApiOnline] = useState(null);
  const [activeTab, setActiveTab] = useState('all'); // all | trending | broad | niche

  // Health check + load initial trending
  useEffect(() => {
    checkHealth().then(ok => {
      setApiOnline(ok);
      if (ok) loadTrending('all');
    });
  }, []);

  const loadTrending = async (p) => {
    try {
      const data = await getTrending(p);
      setTrending(data.trending || []);
    } catch {}
  };

  const handlePlatformChange = (p) => {
    setPlatform(p);
    loadTrending(p);
  };

  const handleGenerate = async () => {
    if (!text.trim() || text.trim().length < 3) return;
    setLoading(true);
    setError('');
    setResult(null);
    setActiveTab('all');
    try {
      const data = await generateHashtags({ text, platform, count });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setText('');
    setError('');
  };

  // Which hashtags to show based on active tab
  const displayedHashtags = result
    ? (activeTab === 'all'      ? result.hashtags
     : activeTab === 'trending' ? result.trending
     : activeTab === 'broad'    ? result.broad
     :                            result.niche)
    : [];

  return (
    <div className="app">
      {/* ── HEADER ── */}
      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <div className="brand-icon">#</div>
            <div>
              <h1 className="brand-name">TagCraft</h1>
              <p className="brand-sub">Automatic Hashtag Generator</p>
            </div>
          </div>

          <div className={`api-badge ${apiOnline === null ? 'pending' : apiOnline ? 'online' : 'offline'}`}>
            <span className="api-dot" />
            {apiOnline === null ? 'Connecting…' : apiOnline ? 'API Online' : 'API Offline'}
          </div>
        </div>

        {/* Platform Selector */}
        <div className="platform-bar">
          {PLATFORMS.map(p => (
            <button
              key={p.id}
              className={`platform-btn ${platform === p.id ? 'active' : ''}`}
              onClick={() => handlePlatformChange(p.id)}
            >
              <span className="platform-icon">{p.icon}</span>
              <span className="platform-label">{p.label}</span>
            </button>
          ))}
        </div>
      </header>

      {/* ── MAIN ── */}
      <main className="main">
        <div className="layout">

          {/* LEFT: Input + Results */}
          <div className="left-col">
            <InputPanel
              text={text}
              setText={setText}
              count={count}
              setCount={setCount}
              onGenerate={handleGenerate}
              onReset={handleReset}
              loading={loading}
              hasResult={!!result}
            />

            {error && <div className="error-box">⚠ {error}</div>}

            {result && (
              <HashtagResults
                result={result}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                displayedHashtags={displayedHashtags}
                platform={platform}
              />
            )}
          </div>

          {/* RIGHT: Trending Sidebar */}
          <div className="right-col">
            <TrendingPanel
              trending={trending}
              platform={platform}
              platforms={PLATFORMS}
              onPlatformChange={handlePlatformChange}
            />
          </div>

        </div>
      </main>

      <footer className="footer">
        <span>TagCraft · Supports Instagram · Twitter/X · LinkedIn · YouTube · GitHub</span>
      </footer>
    </div>
  );
}