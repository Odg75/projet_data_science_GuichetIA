# GuichetIA : Assistant Administratif RAG (Burkina Faso)

> Projet Data Science 2026 - Master 1 Informatique IFOAD - Option 7 : Assistant Juridique et Administratif

Assistant conversationnel intelligent qui répond aux questions sur **6 démarches administratives** burkinabè (CNIB, passeport, casier judiciaire, acte de naissance, certificat de nationalité, création d'entreprise) à partir de sources officielles, via un pipeline RAG (Retrieval-Augmented Generation).

**Auteurs :** DICKO Mamoudou, OUEDRAOGO Abdoul Kader W. Ghislan, OUEDRAOGO Zeïd El Gazeli

## Liens

- **Application en ligne :** https://guichetia.vercel.app
- **Backend API :** https://guichetia-backend.onrender.com
- **Dépôt GitHub :** https://github.com/Odg75/projet_data_science_GuichetIA

## Stack technique

```
Collecte      -> PyMuPDF (lecture des PDFs sources) + generate_source_pdfs.py
Chunking      -> LangChain RecursiveCharacterTextSplitter (500 tokens, overlap 50)
Embeddings    -> sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (HuggingFace Inference API)
Vector DB     -> ChromaDB (métrique cosinus, k=6 chunks)
LLM           -> Llama-3.1-8b-instant via Groq API (température 0.1)
Orchestration -> LangChain
Backend       -> FastAPI + Python
Frontend      -> React 18 + Tailwind CSS v3
Déploiement   -> Render (backend, plan gratuit) + Vercel (frontend)
```

## Structure du projet

```
backend/
  data/
    pdfs/                     -> 6 PDFs sources (un par démarche)
    chroma_db/                -> base vectorielle ChromaDB (générée automatiquement au déploiement)
    generate_source_pdfs.py   -> génère les PDFs depuis les données officielles vérifiées
  ingestion/
    extract_pdf.py            -> extraction du texte des PDFs (PyMuPDF)
    build_index.py            -> chunking + embeddings + indexation dans ChromaDB
  app/
    rag.py                    -> pipeline RAG (retriever, prompt système, LLM)
    main.py                   -> API FastAPI (endpoints /health et /ask)
  evaluation/
    test_questions.json       -> jeu de questions de test (in-scope et out-of-scope)
    evaluate.py               -> mesure pertinence du retrieval + taux d'hallucination
  requirements.txt
  .env.example
frontend/
  src/
    pages/
      Landing.jsx             -> page d'accueil avec statistiques
      ChatDashboard.jsx       -> interface de conversation + suggestions intelligentes
      About.jsx               -> page À propos et architecture
    api.js                    -> client HTTP vers le backend FastAPI
  .env.example
Rapport_Technique_GuichetIA.pdf  -> rapport technique complet (PDF)
```

## Mise en route : Backend

1. Créer un environnement virtuel et installer les dépendances :
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate   # (ou venv\Scripts\activate sous Windows)
   pip install -r requirements.txt
   ```

2. Copier `.env.example` en `.env` et renseigner les clés API :
   ```
   GROQ_API_KEY=ta_cle_groq        # gratuite sur console.groq.com
   HUGGINGFACEHUB_API_TOKEN=...    # gratuite sur huggingface.co
   ```

3. Générer les PDFs sources (si modification du contenu) :
   ```bash
   python data/generate_source_pdfs.py
   ```

4. Construire la base vectorielle :
   ```bash
   python ingestion/build_index.py
   ```

5. Lancer l'API :
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Vérifier sur http://localhost:8000/health et http://localhost:8000/docs

6. (Optionnel) Évaluer le système :
   ```bash
   python evaluation/evaluate.py
   ```

## Mise en route : Frontend

1. Installer les dépendances :
   ```bash
   cd frontend
   npm install
   ```

2. Copier `.env.example` en `.env` :
   ```
   VITE_API_URL=http://localhost:8000
   ```

3. Lancer le serveur de développement :
   ```bash
   npm run dev
   ```

## Déploiement

**Backend (Render) :**
- `render.yaml` à la racine configure automatiquement le service.
- Variables d'environnement à renseigner : `GROQ_API_KEY`, `HUGGINGFACEHUB_API_TOKEN`.
- L'index ChromaDB est reconstruit à chaque déploiement via `build_index.py`.

**Frontend (Vercel) :**
- Projet po