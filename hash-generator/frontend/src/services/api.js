// services/api.js

const BASE = 'http://localhost:5000/api';

export async function generateHashtags({ text, platform, count }) {
  const res = await fetch(`${BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, platform, count }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to generate hashtags');
  return data;
}

export async function getTrending(platform = 'all') {
  const res = await fetch(`${BASE}/trending?platform=${platform}`);
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch trending');
  return data;
}

export async function checkHealth() {
  try {
    const res = await fetch(`${BASE}/health`);
    return res.ok;
  } catch { return false; }
}