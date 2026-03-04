# ReverseLens

Upload an image, get a description — powered by reverse image search + local LLM (Ollama). Fully free, no paid APIs.

## How it works

1. You send an image (upload or URL)
2. Image gets preprocessed (resize, sharpen, contrast)
3. **Agentic loop** kicks in:
   - Agent searches TinEye first
   - Evaluates results with LLM — enough or not?
   - If not enough, tries Yandex → Bing
   - Generates answer, checks quality
   - Regenerates if quality is poor
4. Result saved to SQLite history + JSON cache
5. Authenticated users get higher rate limits + history

## Setup

```bash
cd free_image_agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Ollama:
```bash
brew install ollama
brew services start ollama
ollama pull llama3.1
```

Optional (for async queue):
```bash
brew install redis
brew services start redis
```

## Run

**Terminal 1 — API:**
```bash
python main.py
```

**Terminal 2 — Web UI:**
```bash
streamlit run app.py
```

**Terminal 3 — Celery worker (optional):**
```bash
celery -A services.tasks worker --loglevel=info
```

## Usage

### Web UI (recommended)
Open http://localhost:8501
- Upload tab: drag-n-drop or file picker
- URL tab: paste image link
- History tab: view past analyses (requires login)

### API

**Public (10 req/min):**
```bash
curl -X POST http://localhost:8000/analyze -F "file=@photo.jpg"
```

**With auth (20 req/min + history):**
```bash
# register
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass1234"}'

# analyze
curl -X POST http://localhost:8000/analyze/auth \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@photo.jpg"

# history
curl http://localhost:8000/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Async (requires Redis):**
```bash
curl -X POST http://localhost:8000/analyze/async -F "file=@photo.jpg"
# returns task_id

curl http://localhost:8000/task/TASK_ID
# returns status + result
```

## Features

- 🤖 **Agentic loop** — LLM decides search strategy and evaluates results
- 📤 **Upload** images (drag-n-drop)
- 🔗 **URL support** — paste image link directly
- 🔄 **Multi-engine search** — TinEye → Yandex → Bing
- 🧠 **Local LLM** — Ollama llama3.1, fully offline
- 💾 **Smart cache** — JSON file, same image = instant
- 🗄️ **SQLite database** — search history per user
- 🔐 **JWT auth** — register/login, protected endpoints
- ⏱️ **Rate limiting** — 10/min public, 20/min authenticated
- 📋 **Async queue** — Celery + Redis for background tasks
- 🖼️ **Image preprocessing** — sharpen, contrast, resize
- 🎨 **Streamlit UI** — clean web interface

## Project structure

```
free_image_agent/
├── main.py                # FastAPI + auth + rate limiting + queue
├── app.py                 # Streamlit web UI
├── services/
│   ├── search.py          # TinEye / Yandex / Bing
│   ├── analyze.py         # Ollama LLM
│   ├── agent.py           # Agentic loop orchestrator
│   ├── preprocess.py      # Image enhancement
│   └── tasks.py           # Celery async tasks
├── utils/
│   ├── cache.py           # MD5 hash + JSON cache
│   ├── db.py              # SQLite database
│   └── auth.py            # JWT authentication
├── static/uploads/        # temp images (auto-cleaned)
├── reverselens.db         # SQLite (auto-created)
├── cache.json
└── requirements.txt
```

## Stack

- **Streamlit** — web UI
- **FastAPI** + uvicorn — API backend
- **PicImageSearch** — reverse image search (TinEye, Yandex, Bing)
- **Ollama** llama3.1 — local LLM (free)
- **SQLite** — user history
- **JWT** — authentication
- **slowapi** — rate limiting
- **Celery + Redis** — async task queue
- **Pillow** — image preprocessing


Made with ❤️ by uzbtrust
