import { useEffect, useRef, useState } from "react";
import { askQuestion, checkHealth } from "../api";

// ── Données ──────────────────────────────────────────────────────────────────

const DEMARCHE_LABELS = {
  cnib: "CNIB",
  passeport: "Passeport",
  creation_entreprise: "Création d'entreprise",
  casier_judiciaire: "Casier judiciaire",
  acte_naissance: "Acte de naissance",
  certificat_nationalite: "Certificat de nationalité",
};

const DEMARCHE_COLORS = {
  cnib: "bg-blue-50 text-blue-700 border-blue-200",
  passeport: "bg-purple-50 text-purple-700 border-purple-200",
  creation_entreprise: "bg-amber-50 text-amber-700 border-amber-200",
  casier_judiciaire: "bg-red-50 text-red-700 border-red-200",
  acte_naissance: "bg-teal-50 text-teal-700 border-teal-200",
  certificat_nationalite: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

const SUGGESTIONS = [
  { emoji: "🪪", text: "Quelles pièces pour ma première CNIB ?" },
  { emoji: "✈️", text: "Quelles pièces pour un passeport ordinaire ?" },
  { emoji: "🏢", text: "Comment créer une entreprise individuelle ?" },
  { emoji: "⚖️", text: "Comment obtenir un extrait de casier judiciaire ?" },
];

const WELCOME = "Bonjour ! Je suis GuichetIA, votre assistant pour les démarches administratives au Burkina Faso. Posez-moi votre question.";
const STORAGE_KEY = "guichetia_history_v2";

const THINKING_STEPS = [
  { icon: "🔍", label: "Recherche des documents..." },
  { icon: "📚", label: "Analyse des textes..." },
  { icon: "🧠", label: "Génération de la réponse..." },
];

// ── Utilitaires ───────────────────────────────────────────────────────────────

function genId() { return Date.now().toString(36) + Math.random().toString(36).slice(2); }

function loadHistory() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch { return []; }
}

function saveHistory(h) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(h)); } catch {}
}

function groupByDate(history) {
  const groups = {};
  const today = new Date(); today.setHours(0,0,0,0);
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  history.forEach((conv) => {
    const d = new Date(conv.createdAt); d.setHours(0,0,0,0);
    let key = d >= today ? "Aujourd'hui" : d >= yesterday ? "Hier" : d.toLocaleDateString("fr-FR", { day: "numeric", month: "long" });
    if (!groups[key]) groups[key] = [];
    groups[key].push(conv);
  });
  return groups;
}

function renderWithLinks(text) {
  const parts = [];
  let last = 0;
  const re = /https?:\/\/[^\s,;)\]>"]+/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(
      <a key={m.index} href={m[0]} target="_blank" rel="noopener noreferrer"
        className="underline decoration-dotted text-blue-600 hover:text-blue-800 break-all">
        {m[0]}
      </a>
    );
    last = re.lastIndex;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length ? parts : [text];
}

// ── Composants ────────────────────────────────────────────────────────────────

function PertinenceBar({ score }) {
  const pct = Math.round(score);
  const color = pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-400" : "bg-red-400";
  const label = pct >= 70 ? "Forte" : pct >= 40 ? "Moyenne" : "Faible";
  return (
    <div className="flex items-center gap-2 mt-1">
      <span className="text-[10px] text-slate-500 w-14">Pertinence</span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] font-semibold text-slate-600 w-12 text-right">{pct}% · {label}</span>
    </div>
  );
}

function SourceBadge({ demarche }) {
  const cls = DEMARCHE_COLORS[demarche] || "bg-slate-50 text-slate-600 border-slate-200";
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {DEMARCHE_LABELS[demarche] || demarche}
    </span>
  );
}

function ChatBubble({ role, content, sources, scoreMoyen, chunks, onEdit }) {
  const [copied, setCopied] = useState(false);
  const [showChunks, setShowChunks] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const isUser = role === "user";

  function handleCopy() {
    navigator.clipboard.writeText(content).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  }

  function handleDownload() {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "reponse-guichetia.txt"; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className={`group flex items-end gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="h-8 w-8 flex-shrink-0 rounded-xl bg-gradient-to-br from-blue-700 to-emerald-600 flex items-center justify-center text-white text-[10px] font-bold shadow">
          GIA
        </div>
      )}

      <div className="relative max-w-[80%] space-y-1">
        {/* Action buttons */}
        <div className={`absolute -top-9 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 ${isUser ? "right-0" : "left-0"}`}>
          {!isUser && (
            <>
              <button onClick={handleCopy}
                className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] text-slate-500 hover:text-slate-800 shadow-sm whitespace-nowrap">
                {copied ? "✓ Copié" : "⎘ Copier"}
              </button>
              <button onClick={handleDownload}
                className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] text-slate-500 hover:text-slate-800 shadow-sm whitespace-nowrap">
                ↓ Télécharger
              </button>
            </>
          )}
          {isUser && onEdit && (
            <button onClick={() => onEdit(content)}
              className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] text-slate-500 hover:text-slate-800 shadow-sm">
              ✏ Modifier
            </button>
          )}
        </div>

        {/* Bubble */}
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${
          isUser
            ? "bg-gradient-to-br from-blue-700 to-blue-600 text-white rounded-br-none"
            : "bg-white text-slate-800 border border-slate-100 rounded-bl-none"
        }`}>
          {isUser ? content : <span>{renderWithLinks(content)}</span>}

          {!isUser && sources && sources.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-100 space-y-2">
              <div className="flex flex-wrap gap-1.5">
                {sources.map((s) => <SourceBadge key={s} demarche={s} />)}
              </div>
              {typeof scoreMoyen === "number" && scoreMoyen > 0 && (
                <PertinenceBar score={scoreMoyen} />
              )}
            </div>
          )}
        </div>

        {/* Feedback + voir chunks */}
        {!isUser && (
          <div className="flex items-center gap-2 px-1">
            <button onClick={() => setFeedback("up")}
              className={`text-base transition ${feedback === "up" ? "scale-110" : "opacity-40 hover:opacity-80"}`}
              title="Utile">👍</button>
            <button onClick={() => setFeedback("down")}
              className={`text-base transition ${feedback === "down" ? "scale-110" : "opacity-40 hover:opacity-80"}`}
              title="Non utile">👎</button>
            {chunks && chunks.length > 0 && (
              <button onClick={() => setShowChunks(!showChunks)}
                className="text-[11px] text-blue-600 hover:text-blue-800 transition ml-1">
                {showChunks ? "▲ Masquer" : "📄 Voir les passages utilisés"}
              </button>
            )}
          </div>
        )}

        {/* Chunks panel */}
        {showChunks && chunks && chunks.length > 0 && (
          <div className="space-y-2 mt-1">
            {chunks.map((c, i) => (
              <div key={i} className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs">
                <div className="flex items-center justify-between mb-1.5">
                  <SourceBadge demarche={c.demarche} />
                  <span className="text-slate-400">Score : {c.score}%</span>
                </div>
                <p className="text-slate-600 leading-relaxed line-clamp-4">{c.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ThinkingIndicator({ step }) {
  const s = THINKING_STEPS[step] || THINKING_STEPS[0];
  return (
    <div className="flex items-end gap-2 justify-start">
      <div className="h-8 w-8 flex-shrink-0 rounded-xl bg-gradient-to-br from-blue-700 to-emerald-600 flex items-center justify-center text-white text-[10px] font-bold shadow">GIA</div>
      <div className="bg-white border border-slate-100 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm flex items-center gap-2">
        <span className="text-base">{s.icon}</span>
        <span className="text-sm text-slate-600">{s.label}</span>
        <div className="flex gap-0.5 ml-1">
          {[0,1,2].map((i) => (
            <span key={i} className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: `${i*0.18}s` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── RAG Panel ─────────────────────────────────────────────────────────────────

function RagPanel({ lastResult, loading }) {
  if (!lastResult && !loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-6">
        <div className="text-4xl mb-3">🔬</div>
        <p className="text-sm font-semibold text-slate-700">Analyse RAG</p>
        <p className="text-xs text-slate-400 mt-1">Les métriques apparaîtront après votre première question.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 p-6">
        <div className="h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-500">Analyse en cours...</p>
      </div>
    );
  }

  const { score_moyen, scores, chunks, search_time_ms, gen_time_ms, top_k, llm_model, sources } = lastResult;

  return (
    <div className="p-4 space-y-4 text-sm overflow-y-auto h-full">
      <p className="font-bold text-slate-800 text-xs uppercase tracking-widest">Analyse du système RAG</p>

      {/* Métriques clés */}
      <div className="grid grid-cols-2 gap-2">
        {[
          { label: "Chunks récupérés", value: scores?.length ?? 0 },
          { label: "Top-K configuré", value: top_k ?? 6 },
          { label: "Recherche", value: `${search_time_ms ?? 0} ms` },
          { label: "Génération", value: `${gen_time_ms ?? 0} ms` },
        ].map((m) => (
          <div key={m.label} className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-center">
            <p className="text-base font-extrabold text-blue-700">{m.value}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">{m.label}</p>
          </div>
        ))}
      </div>

      {/* LLM */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
        <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Modèle LLM</p>
        <p className="font-mono text-xs text-slate-700 truncate">{llm_model || "llama-3.1-8b-instant"}</p>
      </div>

      {/* Score de pertinence */}
      {typeof score_moyen === "number" && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-2">Score de confiance</p>
          <PertinenceBar score={score_moyen} />
          {scores && scores.length > 0 && (
            <div className="mt-2 space-y-1">
              {scores.map((s, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400 w-12">Chunk {i+1}</span>
                  <div className="flex-1 h-1 bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-400 rounded-full" style={{ width: `${s}%` }} />
                  </div>
                  <span className="text-[10px] text-slate-500 w-10 text-right">{s}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Démarches identifiées */}
      {sources && sources.length > 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-2">Démarches identifiées</p>
          <div className="flex flex-wrap gap-1">
            {sources.map((s) => <SourceBadge key={s} demarche={s} />)}
          </div>
        </div>
      )}

      {/* Passages */}
      {chunks && chunks.length > 0 && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-2">Documents retrouvés ({chunks.length})</p>
          <div className="space-y-2">
            {chunks.map((c, i) => (
              <div key={i} className="border border-slate-200 bg-white rounded-lg p-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-semibold text-blue-700">{DEMARCHE_LABELS[c.demarche] || c.demarche}</span>
                  <span className="text-[10px] text-slate-400">{c.score}%</span>
                </div>
                <p className="text-[10px] text-slate-500 line-clamp-2 leading-relaxed">{c.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── App Dashboard ─────────────────────────────────────────────────────────────

export default function ChatDashboard({ onNavigate, initialQuestion }) {
  const [history, setHistory] = useState(loadHistory);
  const [currentId, setCurrentId] = useState(null);
  const [messages, setMessages] = useState([{ role: "assistant", content: WELCOME }]);
  const [input, setInput] = useState(initialQuestion || "");
  const [loading, setLoading] = useState(false);
  const [thinkingStep, setThinkingStep] = useState(0);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [ragPanelOpen, setRagPanelOpen] = useState(true);
  const [lastResult, setLastResult] = useState(null);
  const [favorites, setFavorites] = useState(() => {
    try { return JSON.parse(localStorage.getItem("guichetia_favorites") || "[]"); } catch { return []; }
  });
  const [activeSection, setActiveSection] = useState("chat");

  const bottomRef = useRef(null);
  const currentIdRef = useRef(null);
  const thinkingRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { checkHealth().then(setApiStatus); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  // Auto-send si initialQuestion
  useEffect(() => {
    if (initialQuestion) { setTimeout(() => handleSend(initialQuestion), 100); }
  }, []);

  function setConvId(id) { currentIdRef.current = id; setCurrentId(id); }

  function newConversation() {
    setConvId(null);
    setMessages([{ role: "assistant", content: WELCOME }]);
    setInput(""); setError(null); setLastResult(null);
    setSidebarOpen(false); setActiveSection("chat");
  }

  function openConversation(conv) {
    setConvId(conv.id);
    setMessages(conv.messages);
    setInput(""); setError(null);
    setLastResult(conv.lastResult || null);
    setSidebarOpen(false); setActiveSection("chat");
  }

  function deleteConversation(id) {
    setHistory((prev) => { const u = prev.filter((c) => c.id !== id); saveHistory(u); return u; });
    if (currentIdRef.current === id) newConversation();
  }

  function toggleFavorite(id) {
    setFavorites((prev) => {
      const next = prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id];
      localStorage.setItem("guichetia_favorites", JSON.stringify(next));
      return next;
    });
  }

  function handleEdit(msgIndex, content) {
    setMessages((prev) => prev.slice(0, msgIndex));
    setInput(content); setError(null);
  }

  async function handleSend(question) {
    const text = (question ?? input).trim();
    if (!text || loading) return;

    const withUser = [...messages, { role: "user", content: text }];
    setMessages(withUser); setInput(""); setLoading(true); setError(null); setThinkingStep(0);

    let step = 0;
    thinkingRef.current = setInterval(() => {
      step = Math.min(step + 1, THINKING_STEPS.length - 1);
      setThinkingStep(step);
    }, 900);

    try {
      const data = await askQuestion(text);
      clearInterval(thinkingRef.current);
      const assistantMsg = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        scoreMoyen: data.score_moyen,
        chunks: data.chunks || [],
      };
      const finalMsgs = [...withUser, assistantMsg];
      setMessages(finalMsgs);
      setLastResult(data);

      const title = text.slice(0, 55) + (text.length > 55 ? "…" : "");
      let cid = currentIdRef.current;
      if (!cid) { cid = genId(); currentIdRef.current = cid; setCurrentId(cid); }

      setHistory((prev) => {
        const exists = prev.find((c) => c.id === cid);
        const updated = exists
          ? prev.map((c) => c.id === cid ? { ...c, messages: finalMsgs, lastResult: data } : c)
          : [{ id: cid, title, messages: finalMsgs, lastResult: data, createdAt: Date.now() }, ...prev];
        saveHistory(updated);
        return updated;
      });
    } catch (err) {
      clearInterval(thinkingRef.current);
      setError(err.message || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  }

  const grouped = groupByDate(history);
  const isDegraded = apiStatus && apiStatus.status !== "ok";
  const favConvs = history.filter((c) => favorites.includes(c.id));

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-20 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* ── Sidebar ── */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-30 w-64 flex flex-col bg-slate-900 transition-transform duration-200 ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/10">
          <div className="h-9 w-9 flex-shrink-0 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center font-extrabold text-white text-sm shadow">G</div>
          <div>
            <p className="text-white font-bold text-sm leading-none">GuichetIA</p>
            <p className="text-slate-400 text-[11px] mt-0.5">Burkina Faso · v2.0</p>
          </div>
        </div>

        {/* Navigation */}
        <div className="px-3 py-3 space-y-0.5">
          <button onClick={newConversation}
            className="w-full flex items-center gap-2.5 rounded-xl border border-blue-500/40 px-3 py-2.5 text-sm text-blue-400 hover:bg-blue-500/10 transition font-semibold">
            <span className="text-lg">+</span> Nouvelle conversation
          </button>
        </div>

        <div className="px-3 space-y-0.5">
          {[
            { id: "chat", icon: "💬", label: "Conversation" },
            { id: "demarches", icon: "📋", label: "Démarches" },
            { id: "favorites", icon: "⭐", label: "Favoris" },
          ].map((item) => (
            <button key={item.id} onClick={() => setActiveSection(item.id)}
              className={`w-full flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm transition ${activeSection === item.id ? "bg-blue-600/20 text-blue-400 font-semibold" : "text-slate-400 hover:bg-white/5 hover:text-slate-200"}`}>
              <span>{item.icon}</span> {item.label}
            </button>
          ))}
        </div>

        {/* Historique */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 mt-1">
          {activeSection === "favorites" ? (
            favConvs.length === 0
              ? <p className="text-xs text-slate-500 text-center mt-4">Aucun favori</p>
              : favConvs.map((conv) => (
                  <ConvItem key={conv.id} conv={conv} currentId={currentId}
                    onOpen={openConversation} onDelete={deleteConversation}
                    onFav={toggleFavorite} isFav />
                ))
          ) : activeSection === "demarches" ? (
            <div className="space-y-1.5">
              {Object.entries(DEMARCHE_LABELS).map(([key, label]) => (
                <button key={key}
                  onClick={() => { handleSend(`Quelles sont les étapes pour la démarche ${label} ?`); setActiveSection("chat"); }}
                  className="w-full text-left rounded-xl px-3 py-2 text-xs text-slate-400 hover:bg-white/5 hover:text-slate-200 transition">
                  {label}
                </button>
              ))}
            </div>
          ) : (
            Object.keys(grouped).length === 0
              ? <p className="text-xs text-slate-500 text-center mt-4">Aucun historique</p>
              : Object.entries(grouped).map(([date, convs]) => (
                  <div key={date}>
                    <p className="text-[10px] text-slate-500 uppercase tracking-widest px-2 mb-1">{date}</p>
                    <div className="space-y-0.5">
                      {convs.map((conv) => (
                        <ConvItem key={conv.id} conv={conv} currentId={currentId}
                          onOpen={openConversation} onDelete={deleteConversation}
                          onFav={toggleFavorite} isFav={favorites.includes(conv.id)} />
                      ))}
                    </div>
                  </div>
                ))
          )}
        </div>

        {/* Footer nav */}
        <div className="border-t border-white/10 px-3 py-3 space-y-0.5">
          <button onClick={() => onNavigate("about")}
            className="w-full flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-400 hover:bg-white/5 hover:text-slate-200 transition">
            <span>ℹ️</span> À propos
          </button>
          <button onClick={() => onNavigate("landing")}
            className="w-full flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-400 hover:bg-white/5 hover:text-slate-200 transition">
            <span>🏠</span> Accueil
          </button>
        </div>
      </aside>

      {/* ── Zone principale ── */}
      <div className="flex flex-1 overflow-hidden min-w-0">
        {/* Centre : chat */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Header */}
          <header className="flex-shrink-0 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3 shadow-sm">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-slate-500 hover:text-slate-700 p-1 text-xl">≡</button>
            <div className="flex-1 min-w-0">
              <h1 className="text-sm font-bold text-slate-800">Guichet IA Administratif &amp; Juridique</h1>
              <p className="text-xs text-slate-400 truncate">CNIB · Passeport · Entreprise · Casier · Acte de naissance · Nationalité</p>
            </div>
            <div className="flex items-center gap-2">
              {apiStatus && (
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${isDegraded ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                  {isDegraded ? "Dégradé" : "● En ligne"}
                </span>
              )}
              <button onClick={() => setRagPanelOpen(!ragPanelOpen)}
                className="hidden xl:flex items-center gap-1.5 rounded-xl border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 transition">
                🔬 {ragPanelOpen ? "Masquer" : "Analyse RAG"}
              </button>
            </div>
          </header>

          {/* Messages */}
          <main className="flex-1 overflow-y-auto px-4 py-5 bg-slate-50">
            <div className="mx-auto max-w-2xl space-y-4">
              {messages.map((m, i) => (
                <ChatBubble key={i} role={m.role} content={m.content}
                  sources={m.sources} scoreMoyen={m.scoreMoyen} chunks={m.chunks}
                  onEdit={m.role === "user" ? (c) => handleEdit(i, c) : undefined} />
              ))}
              {loading && <ThinkingIndicator step={thinkingStep} />}
              {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
              )}
              {!loading && messages.length <= 1 && (
                <div className="mt-4">
                  <p className="text-[11px] text-slate-400 uppercase tracking-widest font-semibold mb-3">Suggestions</p>
                  <div className="grid grid-cols-2 gap-2">
                    {SUGGESTIONS.map((s) => (
                      <button key={s.text} onClick={() => handleSend(s.text)}
                        className="flex items-start gap-2 rounded-xl border border-slate-200 bg-white px-3 py-3 text-xs text-slate-600 hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 transition shadow-sm text-left">
                        <span className="text-lg flex-shrink-0">{s.emoji}</span>
                        <span>{s.text}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </main>

          {/* Search bar */}
          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex-shrink-0 bg-white border-t border-slate-200 px-4 py-3">
            <div className="mx-auto max-w-2xl">
              <div className="flex items-center gap-2 bg-slate-50 border border-slate-300 rounded-2xl px-3 py-2 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 transition shadow-sm">
                <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)}
                  placeholder="Posez votre question sur une démarche administrative..."
                  className="flex-1 bg-transparent text-sm outline-none text-slate-800 placeholder-slate-400"
                  disabled={loading} />
                {input && (
                  <button type="button" onClick={() => setInput("")}
                    className="text-slate-400 hover:text-slate-600 transition text-lg leading-none" title="Effacer">
                    ×
                  </button>
                )}
                <button type="submit" disabled={loading || !input.trim()}
                  className="bg-blue-700 hover:bg-blue-800 text-white rounded-xl px-4 py-1.5 text-sm font-semibold disabled:opacity-50 transition shadow flex-shrink-0">
                  Envoyer
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* ── RAG Panel ── */}
        {ragPanelOpen && (
          <aside className="hidden xl:flex w-72 flex-shrink-0 flex-col border-l border-slate-200 bg-white overflow-hidden">
            <div className="flex-shrink-0 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-widest">Analyse RAG</span>
              <button onClick={() => setRagPanelOpen(false)} className="text-slate-400 hover:text-slate-600 text-lg leading-none">×</button>
            </div>
            <RagPanel lastResult={lastResult} loading={loading} />
          </aside>
        )}
      </div>
    </div>
  );
}

// ── ConvItem (item d'historique) ──────────────────────────────────────────────

function ConvItem({ conv, currentId, onOpen, onDelete, onFav, isFav }) {
  return (
    <div onClick={() => onOpen(conv)}
      className={`group flex items-center justify-between rounded-xl px-3 py-2 cursor-pointer transition ${conv.id === currentId ? "bg-blue-600/20 text-blue-400 font-semibold" : "text-slate-400 hover:bg-white/5 hover:text-slate-200"}`}>
      <span className="truncate flex-1 text-xs">{conv.title}</span>
      <div className="flex items-center gap-1 ml-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition">
        <button onClick={(e) => { e.stopPropagation(); onFav(conv.id); }}
          className={`text-sm ${isFav ? "text-amber-400" : "text-slate-500 hover:text-amber-300"}`}>
          {isFav ? "★" : "☆"}
        </button>
        <button onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
          className="text-slate-500 hover:text-red-400 text-xs">✕</button>
      </div>
    </div>
  );
}
