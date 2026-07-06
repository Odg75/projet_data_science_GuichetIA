import { useEffect, useRef, useState } from "react";
import { askQuestion, checkHealth } from "./api";

// --- Données ---

const DEMARCHE_LABELS = {
  cnib: "CNIB",
  passeport: "Passeport",
  creation_entreprise: "Création d'entreprise",
  casier_judiciaire: "Casier judiciaire",
  acte_naissance: "Acte de naissance",
  certificat_nationalite: "Certificat de nationalité",
};

const SUGGESTIONS = [
  "Quelles pièces pour ma première CNIB ?",
  "Combien coûte un passeport ordinaire ?",
  "Comment créer une entreprise individuelle ?",
  "Comment obtenir un extrait de casier judiciaire ?",
];

const WELCOME =
  "Bonjour ! Je suis GuichetIA, votre assistant pour les démarches administratives au Burkina Faso : CNIB, passeport, création d'entreprise et casier judiciaire. Posez-moi votre question.";

const STORAGE_KEY = "guichetia_history";

// --- Utilitaires ---

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistory(h) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(h));
  } catch {}
}

/** Transforme les URLs dans un texte en liens cliquables. */
function renderWithLinks(text) {
  const parts = [];
  let last = 0;
  const re = /https?:\/\/[^\s,;)\]>"]+/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(
      <a
        key={m.index}
        href={m[0]}
        target="_blank"
        rel="noopener noreferrer"
        className="underline decoration-dotted text-[#FCD116] hover:text-amber-300 break-all"
      >
        {m[0]}
      </a>
    );
    last = re.lastIndex;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length ? parts : [text];
}

// --- Composants ---

function SourceBadge({ demarche }) {
  return (
    <span className="inline-flex items-center rounded-full border border-[#FCD116]/50 bg-[#FCD116]/15 px-2.5 py-0.5 text-xs font-medium text-amber-800">
      {DEMARCHE_LABELS[demarche] || demarche}
    </span>
  );
}

function ChatBubble({ role, content, sources, scoreMoyen, onEdit }) {
  const [copied, setCopied] = useState(false);
  const isUser = role === "user";

  function handleCopy() {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className={`group flex items-end gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="h-7 w-7 flex-shrink-0 rounded-full bg-[#009A44] flex items-center justify-center text-white text-[10px] font-bold shadow-sm">
          GIA
        </div>
      )}
      <div className="relative max-w-[78%]">
        {/* Boutons d'action (visibles au survol) */}
        <div className={`absolute -top-8 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity ${isUser ? "right-0" : "left-0"}`}>
          {!isUser && (
            <button
              onClick={handleCopy}
              className="rounded-lg border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-500 hover:text-gray-800 shadow-sm whitespace-nowrap"
            >
              {copied ? "✓ Copié" : "⎘ Copier"}
            </button>
          )}
          {isUser && onEdit && (
            <button
              onClick={() => onEdit(content)}
              className="rounded-lg border border-gray-200 bg-white px-2 py-1 text-[11px] text-gray-500 hover:text-gray-800 shadow-sm whitespace-nowrap"
            >
              ✏ Modifier
            </button>
          )}
        </div>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${
            isUser
              ? "bg-[#009A44] text-white rounded-br-none"
              : "bg-white text-gray-800 border border-gray-100 rounded-bl-none"
          }`}
        >
          {isUser ? content : <span>{renderWithLinks(content)}</span>}
          {sources && sources.length > 0 && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-gray-100 pt-2">
              {sources.map((s) => (
                <SourceBadge key={s} demarche={s} />
              ))}
              {typeof scoreMoyen === "number" && scoreMoyen > 0 && (
                <span
                  className="inline-flex items-center rounded-full border border-gray-200 bg-gray-50 px-2 py-0.5 text-[10px] text-gray-400"
                  title="Score moyen de pertinence des passages récupérés (0-100)"
                >
                  Pertinence {scoreMoyen.toFixed(0)}%
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 justify-start">
      <div className="h-7 w-7 flex-shrink-0 rounded-full bg-[#009A44] flex items-center justify-center text-white text-[10px] font-bold shadow-sm">
        GIA
      </div>
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-none bg-white border border-gray-100 px-4 py-3 shadow-sm">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full bg-[#009A44] animate-bounce"
            style={{ animationDelay: `${i * 0.18}s` }}
          />
        ))}
      </div>
    </div>
  );
}

// --- App principale ---

export default function App() {
  const [history, setHistory] = useState(loadHistory);
  const [currentId, setCurrentId] = useState(null);
  const [messages, setMessages] = useState([{ role: "assistant", content: WELCOME }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef(null);
  const currentIdRef = useRef(null);

  useEffect(() => {
    checkHealth().then(setApiStatus);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function setConvId(id) {
    currentIdRef.current = id;
    setCurrentId(id);
  }

  function newConversation() {
    setConvId(null);
    setMessages([{ role: "assistant", content: WELCOME }]);
    setInput("");
    setError(null);
    setSidebarOpen(false);
  }

  function openConversation(conv) {
    setConvId(conv.id);
    setMessages(conv.messages);
    setInput("");
    setError(null);
    setSidebarOpen(false);
  }

  function deleteConversation(id) {
    setHistory((prev) => {
      const updated = prev.filter((c) => c.id !== id);
      saveHistory(updated);
      return updated;
    });
    if (currentIdRef.current === id) newConversation();
  }

  function handleEdit(msgIndex, content) {
    // Supprime le message et tout ce qui suit, remet le texte dans le champ
    setMessages((prev) => prev.slice(0, msgIndex));
    setInput(content);
    setError(null);
  }

  async function handleSend(question) {
    const text = (question ?? input).trim();
    if (!text || loading) return;

    const withUser = [...messages, { role: "user", content: text }];
    setMessages(withUser);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const data = await askQuestion(text);
      const finalMsgs = [
        ...withUser,
        { role: "assistant", content: data.answer, sources: data.sources, scoreMoyen: data.score_moyen },
      ];
      setMessages(finalMsgs);

      const title = text.slice(0, 55) + (text.length > 55 ? "…" : "");
      let cid = currentIdRef.current;
      if (!cid) {
        cid = genId();
        currentIdRef.current = cid;
        setCurrentId(cid);
      }

      setHistory((prev) => {
        const exists = prev.find((c) => c.id === cid);
        const updated = exists
          ? prev.map((c) => (c.id === cid ? { ...c, messages: finalMsgs } : c))
          : [{ id: cid, title, messages: finalMsgs, createdAt: Date.now() }, ...prev];
        saveHistory(updated);
        return updated;
      });
    } catch (err) {
      setError(err.message || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  }

  const isDegraded = apiStatus && apiStatus.status !== "ok";

  return (
    <div className="flex h-screen overflow-hidden bg-[#F4FAF6]">
      {/* Overlay mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/40 sm:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed sm:static inset-y-0 left-0 z-30 w-64 flex flex-col bg-[#003d1c] transition-transform duration-200 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0"
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 border-b border-white/10 px-4 py-4">
          <div className="h-9 w-9 flex-shrink-0 rounded-full bg-[#FCD116] flex items-center justify-center font-extrabold text-[#003d1c] text-base shadow">
            G
          </div>
          <div>
            <p className="text-white font-bold text-sm leading-none">GuichetIA</p>
            <p className="text-green-300 text-[11px] mt-0.5">Burkina Faso</p>
          </div>
        </div>

        {/* Nouvelle conversation */}
        <div className="px-3 py-3">
          <button
            onClick={newConversation}
            className="w-full rounded-lg border border-[#FCD116]/40 px-3 py-2 text-sm text-[#FCD116] hover:bg-[#FCD116]/10 transition flex items-center gap-2 font-medium"
          >
            <span className="text-lg leading-none">+</span>
            Nouvelle conversation
          </button>
        </div>

        {/* Historique */}
        <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-0.5">
          {history.length === 0 ? (
            <p className="text-center text-xs text-green-400/50 mt-6 px-2">
              Aucun historique
            </p>
          ) : (
            history.map((conv) => (
              <div
                key={conv.id}
                onClick={() => openConversation(conv)}
                className={`group flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer transition ${
                  conv.id === currentId
                    ? "bg-[#FCD116]/20 text-[#FCD116] font-medium"
                    : "text-gray-300 hover:bg-white/10"
                }`}
              >
                <span className="truncate flex-1 text-xs">{conv.title}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  className="ml-2 flex-shrink-0 opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition text-xs"
                  title="Supprimer"
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>

        {/* Pied de page sidebar */}
        <div className="border-t border-white/10 px-4 py-3 text-[10px] text-green-400/50 text-center">
          Master 1 IFOAD · Data Science · 2026
        </div>
      </aside>

      {/* Zone principale */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        {/* En-tête */}
        <header className="flex-shrink-0 border-b border-gray-200 bg-white px-4 py-3 flex items-center gap-3 shadow-sm">
          <button
            onClick={() => setSidebarOpen(true)}
            className="sm:hidden text-gray-500 hover:text-gray-700 p-1 text-xl"
            aria-label="Ouvrir le menu"
          >
            ≡
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-bold text-[#003d1c]">GuichetIA</h1>
            <p className="text-xs text-gray-400 truncate">
              CNIB · Passeport · Création d'entreprise · Casier judiciaire
            </p>
          </div>
          {apiStatus && (
            <span
              className={`flex-shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                isDegraded
                  ? "bg-amber-100 text-amber-700"
                  : "bg-green-100 text-green-700"
              }`}
              title={isDegraded ? "Service partiellement indisponible" : "API opérationnelle"}
            >
              {isDegraded ? "Dégradé" : "● En ligne"}
            </span>
          )}
        </header>

        {/* Messages */}
        <main className="flex-1 overflow-y-auto px-4 py-5">
          <div className="mx-auto max-w-2xl space-y-4">
            {messages.map((m, i) => (
              <ChatBubble
                key={i}
                role={m.role}
                content={m.content}
                sources={m.sources}
                scoreMoyen={m.scoreMoyen}
                onEdit={m.role === "user" ? (content) => handleEdit(i, content) : undefined}
              />
            ))}
            {loading && <TypingIndicator />}
            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}
            {!loading && (
              <div className="mt-2">
                <p className="text-[11px] text-gray-400 uppercase tracking-wide font-semibold mb-2">
                  Suggestions
                </p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSend(s)}
                      className="rounded-xl border border-[#009A44]/30 bg-white px-3 py-2 text-xs text-gray-600 hover:border-[#009A44] hover:bg-[#009A44]/5 hover:text-[#003d1c] transition shadow-sm"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </main>

        {/* Saisie */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex-shrink-0 border-t border-gray-200 bg-white px-4 py-3"
        >
          <div className="mx-auto max-w-2xl flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Posez votre question…"
              className="flex-1 rounded-xl border border-gray-300 px-4 py-2.5 text-sm outline-none focus:border-[#009A44] focus:ring-2 focus:ring-[#009A44]/20 transition"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="rounded-xl bg-[#009A44] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#007A35] disabled:opacity-50 disabled:cursor-not-allowed transition shadow"
            >
              Envoyer
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
