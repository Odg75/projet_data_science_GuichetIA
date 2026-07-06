export default function Landing({ onStart, onStartWithQuestion }) {
  const demarches = [
    { emoji: "🪪", label: "CNIB", question: "Quelles pièces pour ma première CNIB ?" },
    { emoji: "✈️", label: "Passeport", question: "Quelles pièces pour un passeport ordinaire ?" },
    { emoji: "👶", label: "Acte de naissance", question: "Comment obtenir une copie de mon acte de naissance ?" },
    { emoji: "⚖️", label: "Casier judiciaire", question: "Comment obtenir un extrait de casier judiciaire ?" },
    { emoji: "🏢", label: "Création d'entreprise", question: "Comment créer une entreprise individuelle via le CEFORE ?" },
    { emoji: "🇧🇫", label: "Certificat de nationalité", question: "Quelles pièces pour un certificat de nationalité burkinabè ?" },
  ];

  const stats = [
    { value: "6", label: "Démarches couvertes" },
    { value: "32", label: "Chunks indexés" },
    { value: "100%", label: "Précision retrieval" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-emerald-50 flex flex-col">
      {/* Nav */}
      <nav className="bg-white/80 backdrop-blur border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-blue-700 to-emerald-600 flex items-center justify-center text-white font-extrabold text-sm shadow">G</div>
            <div>
              <p className="text-sm font-bold text-slate-800 leading-none">GuichetIA</p>
              <p className="text-[10px] text-slate-400 leading-none mt-0.5">Burkina Faso</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => onStart("about")} className="text-sm text-slate-500 hover:text-slate-800 transition px-3 py-1.5">À propos</button>
            <button onClick={onStart} className="bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold px-4 py-2 rounded-xl transition shadow">Commencer</button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 py-20">
        <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          Système RAG opérationnel
        </div>

        <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-blue-700 to-emerald-600 flex items-center justify-center text-white font-extrabold text-3xl shadow-xl mb-6">G</div>

        <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 leading-tight max-w-3xl mb-4">
          Guichet <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-700 to-emerald-600">IA</span> Administratif &amp; Juridique
        </h1>
        <p className="text-lg text-slate-500 max-w-xl mb-8 leading-relaxed">
          Votre assistant intelligent pour toutes les démarches administratives et juridiques du Burkina Faso.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 mb-12">
          <button
            onClick={onStart}
            className="bg-gradient-to-r from-blue-700 to-blue-600 hover:from-blue-800 hover:to-blue-700 text-white font-bold px-8 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition text-base"
          >
            Commencer
          </button>
          <button
            onClick={() => onStart("about")}
            className="border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold px-6 py-3.5 rounded-xl transition text-base"
          >
            En savoir plus
          </button>
        </div>

        {/* Stats */}
        <div className="flex gap-8 mb-16">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-2xl font-extrabold text-blue-700">{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Démarches cards */}
        <div className="w-full max-w-4xl">
          <h2 className="text-lg font-bold text-slate-700 mb-4">Nos principales démarches</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {demarches.map((d) => (
              <button
                key={d.label}
                onClick={() => onStartWithQuestion(d.question)}
                className="group bg-white border border-slate-200 hover:border-blue-300 hover:shadow-md rounded-2xl p-4 text-left transition cursor-pointer"
              >
                <span className="text-2xl block mb-2">{d.emoji}</span>
                <p className="font-semibold text-slate-800 text-sm group-hover:text-blue-700 transition">{d.label}</p>
                <p className="text-xs text-slate-400 mt-0.5">Voir les démarches</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white/60 py-4 text-center text-xs text-slate-400">
        Master 1 IFOAD · Data Science 2026 · Dr Delwende D. Arthur Sawadogo
      </footer>
    </div>
  );
}
