/**
 * Client minimal pour l'API GuichetIA (FastAPI).
 * VITE_API_URL pointe vers le backend (http://localhost:8000 en dev,
 * URL Render en production - voir .env.example).
 */
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function askQuestion(question) {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Erreur ${res.status}`);
  }

  return res.json(); // { answer, sources }
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_URL}/health`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
