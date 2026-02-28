# ReverseLens

Upload an image, get a description — powered by reverse image search + local LLM (Ollama). Fully free, no paid APIs.

## How it works

1. You send an image to `/analyze` endpoint
2. Image gets resized to 512x512 and hashed (for caching)
3. Reverse image search runs via **TinEye** (fallback: Yandex → Bing)
4. Search results (titles, URLs) are sent to **Ollama** (llama3.1)
5. LLM generates a short description in Uzbek based on what the internet says about the image
6. Result is cached so the same image won't be searched again

## Setup

```bash
cd free_image_agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Install and start Ollama:
```bash
brew install ollama
brew services start ollama
ollama pull llama3.1
```

## Run

**Terminal 1 — API Server:**
```bash
python main.py
```
Server starts at `http://localhost:8000`

**Terminal 2 — Streamlit UI:**
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

## Usage

### Via Web UI (recommended)
1. Open http://localhost:8501
2. Upload image or paste URL
3. Click "Analyze"
4. Get instant description + sources

### Via API (curl)
```bash
curl -X POST http://localhost:8000/analyze -F "file=@photo.jpg"
```

Response:
```json
{
  "answer": "Qizil olma, stol ustida yotibdi",
  "sources": [
    {"title": "Red Apple on Table", "url": "https://example.com/..."}
  ],
  "cached": false
}
```

## Project structure

```
free_image_agent/
├── main.py              # FastAPI app
├── services/
│   ├── search.py        # TinEye / Yandex / Bing reverse search
│   └── analyze.py       # Ollama LLM integration
├── utils/
│   └── cache.py         # MD5 hash + JSON file cache
├── static/uploads/      # temp image storage (auto-cleaned)
├── cache.json
└── requirements.txt
```

## Features

- 📤 **Upload** images (drag-n-drop support)
- 🔗 **URL support** — paste image link directly
- 🔄 **Reverse image search** via TinEye (+ Yandex/Bing fallback)
- 🤖 **Local LLM** — Ollama llama3.1, fully offline
- 💾 **Smart cache** — same image = instant result
- 🎨 **Clean UI** — Streamlit web app
- 🆓 **100% free** — no API keys, no subscriptions

## Stack

- **Streamlit** — web UI
- **FastAPI** + uvicorn — API backend
- **PicImageSearch** (TinEye, Yandex, Bing engines)
- **Ollama** with llama3.1 (local, free)
- **Pillow** for image processing


Made with ❤️ by uzbtrust
