import { useEffect, useRef, useState } from "react";
import { askQuestion, checkHealth } from "./api";

const DEMARCHE_LABELS = {
  cnib: "CNIB",
  passeport: "Passeport",
  creation_entreprise: "Création d'entreprise",
  casier_judiciaire: "Casier judiciaire",
};

const SUGGESTIONS = [
  "Quelles pièces pour faire ma première CNIB ?",
  "Combien coûte un passeport ordinaire et en combien de temps ?",
  "Comment créer une entreprise individuelle au Burkina Faso ?",
  "Comment obtenir un extrait de casier judiciaire ?",
];

function SourceBadge({ demarche }) {
  return (
    <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
      {DEMARCHE_LABELS[demarche] || demarche}
    </span>
  );
}

function ChatBubble({ role, content, sources }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-emerald-600 text-white rounded-br-sm"
            : "bg-white text-gray-800 border border-gray-200 rounded-bl-sm shadow-sm"
        }`}
      >
        {content}
        {sources && sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5 border-t border-gray-100 pt-2">
            {sources.map((s) => (
              <SourceBadge key={s} demarche={s} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-sm border border-gray-200 bg-white px-4 py-3 shadow-sm">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Bonjour ! Je suis GuichetIA, votre assistant pour les démarches administratives au Burkina Faso : CNIB, passeport, création d'entreprise et casier judiciaire. Posez-moi une question.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    checkHealth().then(setApiStatus);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(question) {
    const text = (question ?? input).trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const data = await askQuestion(text);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setError(err.message || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    handleSend();
  }

  const isDegraded = apiStatus && apiStatus.status !== "ok";

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">GuichetIA</h1>
            <p className="text-xs text-gray-500">
              Assistant administratif — CNIB · Passeport · Création d'entreprise · Casier judiciaire
            </p>
          </div>
          {apiStatus && (
            <span
              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                isDegraded
                  ? "bg-amber-100 text-amber-800"
                  : "bg-emerald-100 text-emerald-800"
              }`}
              title={
                isDegraded
                  ? "Index vectoriel ou clé API Groq non disponible côté serveur"
                  : "API opérationnelle"
              }
            >
              {isDegraded ? "Service partiellement indisponible" : "En ligne"}
            </span>
          )}
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-3 px-4 py-6 sm:px-6">
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} sources={m.sources} />
        ))}
        {loading && <TypingIndicator />}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        <div ref={bottomRef} />

        {messages.length === 1 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleSend(s)}
                className="rounded-full border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-600 transition hover:border-emerald-400 hover:text-emerald-700"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </main>

      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 border-t border-gray-200 bg-white px-4 py-3 sm:px-6"
      >
        <div className="mx-auto flex max-w-3xl items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question (ex : quelles pièces pour renouveler ma CNIB ?)"
            className="flex-1 rounded-full border border-gray-300 px-4 py-2.5 text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-full bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Envoyer
          </button>
        </div>
      </form>
    </div>
  );
}
