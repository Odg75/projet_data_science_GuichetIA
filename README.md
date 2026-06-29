# GuichetIA — Assistant administratif RAG (Burkina Faso)

Assistant conversationnel qui répond aux questions sur trois démarches administratives (CNIB, passeport, création d'entreprise) à partir de sources officielles, via un pipeline RAG (Retrieval-Augmented Generation).

## Stack technique

```
Collecte      -> PyMuPDF (lecture des PDFs sources)
Chunking      -> LangChain TextSplitter
Embeddings    -> sentence-transformers (HuggingFace, gratuit)
Vector DB     -> ChromaDB (local, persistant)
LLM           -> Groq API (gratuit, rapide)
Orchestration -> LangChain
Backend       -> FastAPI + Python
Frontend      -> React + Tailwind CSS
Déploiement   -> Render (backend) + Vercel (frontend)
```

## Structure du projet

```
backend/
  data/
    pdfs/             -> PDFs sources (un par démarche, générés via generate_source_pdfs.py)
    chroma_db/        -> base vectorielle persistée (générée automatiquement)
    generate_source_pdfs.py -> compile le contenu officiel vérifié en 3 PDFs
  ingestion/
    extract_pdf.py    -> extraction du texte des PDFs (PyMuPDF)
    build_index.py    -> chunking + embeddings + indexation dans Chroma
  app/
    rag.py            -> logique RAG (retriever, LLM, prompt système)
    main.py           -> API FastAPI (endpoints /health et /ask)
  evaluation/
    test_questions.json -> jeu de questions pour évaluer le système
    evaluate.py       -> exécute les questions et affiche réponses + sources
  requirements.txt
  .env.example
frontend/
  src/
    App.jsx           -> interface de chat (React + Tailwind)
    api.js            -> client HTTP vers le backend FastAPI
  .env.example
report/
  (rapport technique final, à rédiger en fin de projet)
```

## Mise en route — Backend

1. Créer un environnement virtuel et installer les dépendances :
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate   (ou venv\Scripts\activate sous Windows)
   pip install -r requirements.txt
   ```
2. Copier `.env.example` en `.env` et renseigner ta clé API Groq (gratuite sur console.groq.com) :
   ```
   GROQ_API_KEY=ta_cle_ici
   ```
3. Générer les PDFs sources (déjà fait, à relancer seulement si le contenu change) :
   ```
   python data/generate_source_pdfs.py
   ```
4. Construire la base vectorielle à partir des PDFs :
   ```
   python ingestion/build_index.py
   ```
5. Lancer l'API :
   ```
   uvicorn app.main:app --reload --port 8000
   ```
   Vérifier sur http://localhost:8000/health et http://localhost:8000/docs
6. (Optionnel) Évaluer le système :
   ```
   python evaluation/evaluate.py
   ```

## Mise en route — Frontend

1. Installer les dépendances :
   ```
   cd frontend
   npm install
   ```
2. Copier `.env.example` en `.env` (l'URL par défaut pointe vers le backend local) :
   ```
   VITE_API_URL=http://localhost:8000
   ```
3. Lancer le serveur de dev :
   ```
   npm run dev
   ```

## Déploiement

**Backend (Render) :**
1. Créer un nouveau Web Service sur Render, connecté au repo Git.
2. Render détecte automatiquement `render.yaml` à la racine (Blueprint). Sinon, configurer manuellement :
   `rootDir: backend`, build = `pip install -r requirements.txt && python ingestion/build_index.py`,
   start = `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Renseigner la variable d'environnement `GROQ_API_KEY` dans les paramètres du service.

**Frontend (Vercel) :**
1. Importer le repo sur Vercel, en pointant le projet vers le dossier `frontend/`.
2. Vercel détecte Vite automatiquement (`vercel.json` présent par sécurité).
3. Renseigner la variable d'environnement `VITE_API_URL` avec l'URL du backend Render
   (ex : `https://guichetia-backend.onrender.com`).

## Ordre de travail conseillé (solo)

Comme le pipeline est le même pour les trois démarches, le plus efficace est de traiter une démarche de bout en bout d'abord (PDF -> index -> test via l'API), puis de répéter pour les deux autres en réutilisant le même code. Cela donne rapidement une version fonctionnelle (même limitée) à montrer, ce qui est plus sûr qu'un système incomplet sur les trois démarches en même temps.
