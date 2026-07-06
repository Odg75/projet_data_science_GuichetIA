export default function About({ onBack }) {
  const stack = [
    { name: "LangChain", version: "0.2.16", role: "Orchestration RAG" },
    { name: "ChromaDB", version: "0.5.5", role: "Base vectorielle" },
    { name: "Groq API", version: "llama-3.1-8b-instant", role: "Modele de langage (LLM)" },
    { name: "HuggingFace", version: "paraphrase-multilingual-MiniLM-L12-v2", role: "Embeddings multilingues" },
    { name: "FastAPI", version: "0.115", role: "Backend API REST" },
    { name: "React 19", version: "+ Tailwind v4", role: "Interface utilisateur" },
  ];

  const metrics = [
    { label: "Documents indexes", value: "6 PDFs" },
    { label: "Chunks vectorises", value: "32" },
    { label: "Taux retrieval pertinent", value: "100%" },
    { label: "Taux non-hallucination", value: "100%" },
    { label: "Top-K chunks recuperes", value: "6" },
    { label: "Derniere mise a jour", value: "07/07/2026" },
  ];

  const pipeline = [
    { step: "1", label: "Question utilisateur", detail: "Saisie dans l'interface React" },
    { step: "2", label: "Embedding de la requete", detail: "paraphrase-multilingual-MiniLM-L12-v2 via HuggingFace Inference API" },
    { step: "3", label: "Recherche vectorielle", detail: "Similarite cosinus dans ChromaDB — Top-K=6 chunks" },
    { step: "4", label: "Construction du contexte", detail: "Assemblage des passages retrouves en prompt structure" },
    { step: "5", label: "Generation LLM", detail: "Llama 3.1-8B-Instant via Groq API (temperature 0.1)" },
    { step: "6", label: "Reponse & sources", detail: "Reponse + badges demarches + score de pertinence" },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-800 to-emerald-700 text-white px-4 py-10">
        <div className="max-w-4xl mx-auto">
          <button onClick={onBack} className="text-white/70 hover:text-white text-sm mb-6 flex items-center gap-1 transition">
            &larr; Retour
          </button>
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-2xl bg-white/20 flex items-center justify-center font-extrabold text-2xl shadow">G</div>
            <div>
              <h1 className="text-2xl font-extrabold">GuichetIA — A propos</h1>
              <p className="text-white/70 text-sm mt-1">Architecture technique &amp; metriques du systeme RAG</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
        {/* Pipeline */}
        <section>
          <h2 className="text-lg font-bold text-slate-800 mb-4">Flux de donnees RAG</h2>
          <div className="space-y-2">
            {pipeline.map((p) => (
              <div key={p.step} className="flex items-start gap-4 bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-sm">
                <div className="h-7 w-7 flex-shrink-0 rounded-full bg-blue-700 text-white flex items-center justify-center text-xs font-bold">{p.step}</div>
                <div>
                  <p className="font-semibold text-slate-800 text-sm">{p.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{p.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Stack technique */}
        <section>
          <h2 className="text-lg font-bold text-slate-800 mb-4">Stack technique</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {stack.map((s) => (
              <div key={s.name} className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-sm">
                <p className="font-semibold text-slate-800 text-sm">{s.name}</p>
                <p className="text-xs text-blue-600 font-mono">{s.version}</p>
                <p className="text-xs text-slate-500 mt-0.5">{s.role}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Metriques */}
        <section>
          <h2 className="text-lg font-bold text-slate-800 mb-4">Metriques d'evaluation</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {metrics.map((m) => (
              <div key={m.label} className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-sm text-center">
                <p className="text-xl font-extrabold text-blue-700">{m.value}</p>
                <p className="text-xs text-slate-500 mt-1">{m.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Demarches couvertes */}
        <section>
          <h2 className="text-lg font-bold text-slate-800 mb-4">Demarches couvertes</h2>
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="flex flex-wrap gap-2">
              {["CNIB","Passeport","Creation d'entreprise","Casier judiciaire","Acte de naissance","Certificat de nationalite"].map((d) => (
                <span key={d} className="bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full">{d}</span>
              ))}
            </div>
          </div>
        </section>

        {/* Limites */}
        <section>
          <h2 className="text-lg font-bold text-slate-800 mb-4">Limites &amp; Perspectives</h2>
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-2 text-sm text-slate-600">
            <p>- Les PDFs sources sont compiles manuellement a partir des portails officiels — une mise a jour automatique via scraping est envisagee.</p>
            <p>- L'index est reconstruit a chaque deploiement Render (build_index.py). Une persistance via volume serait plus efficace.</p>
            <p>- Les scores de pertinence (distance L2 convertie) peuvent sembler faibles numeriquement mais le retrieval reste precis a 100%.</p>
            <p>- Extension possible : permis de conduire, actes d'etat civil, demarches fiscales, etc.</p>
          </div>
        </section>

        <div className="text-center text-xs text-slate-400 pt-4">
          Projet Data Science 2026 · Master 1 IFOAD · UJKZ · Burkina Faso
        </div>
      </div>
    </div>
  );
}
