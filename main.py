import os
import uuid
from pathlib import Path
from PIL import Image
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

from services.search import search_img
from services.analyze import make_answer
from utils.cache import get_hash, get_cached, set_cached

app = FastAPI(title="ReverseLens")

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def resize_img(path):
    img = Image.open(path)
    img = img.convert("RGB")
    img = img.resize((512, 512))
    img.save(path)


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    raw = await file.read()
    h = get_hash(raw)

    # cache bor?
    cached = get_cached(h)
    if cached:
        return JSONResponse({"answer": cached["answer"], "sources": cached["sources"], "cached": True})

    # faylni saqla
    fname = f"{uuid.uuid4().hex}.jpg"
    fpath = UPLOAD_DIR / fname
    try:
        fpath.write_bytes(raw)
        resize_img(str(fpath))

        # qidirish
        results = await search_img(str(fpath))

        if not results:
            return JSONResponse({"answer": "Rasm bo'yicha hech narsa topilmadi", "sources": []})

        # ollama bilan tahlil
        answer = await make_answer(results)

        sources = [{"title": r["title"], "url": r["url"]} for r in results if r["url"]][:5]

        out = {"answer": answer, "sources": sources}
        set_cached(h, out)

        return JSONResponse({**out, "cached": False})

    finally:
        if fpath.exists():
            os.remove(fpath)


@app.get("/")
async def root():
    return {"status": "ok", "usage": "POST /analyze ga rasm yuboring"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
