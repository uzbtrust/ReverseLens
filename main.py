import os
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Depends, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from services.agent import run_agent
from services.preprocess import preprocess
from utils.cache import get_hash, get_cached, set_cached
from utils.auth import hash_pw, check_pw, create_token, get_current_user
from utils.db import add_user, get_user, save_history, get_history

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ReverseLens")
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse({"error": "So'rovlar limiti oshdi. Biroz kuting."}, status_code=429)

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============ AUTH ============

@app.post("/register")
async def register(request: Request):
    body = await request.json()
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    if not username or not password:
        return JSONResponse({"error": "username va password kerak"}, 400)
    if len(password) < 4:
        return JSONResponse({"error": "parol kamida 4 ta belgi"}, 400)
    ok = add_user(username, hash_pw(password))
    if not ok:
        return JSONResponse({"error": "bu username band"}, 409)
    user = get_user(username)
    token = create_token(user["id"], username)
    return {"token": token, "username": username}


@app.post("/login")
async def login(request: Request):
    body = await request.json()
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    user = get_user(username)
    if not user or not check_pw(password, user["pw_hash"]):
        return JSONResponse({"error": "login yoki parol noto'g'ri"}, 401)
    token = create_token(user["id"], username)
    return {"token": token, "username": username}


# ============ ANALYZE ============

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze(request: Request, file: UploadFile = File(...)):
    raw = await file.read()
    h = get_hash(raw)

    cached = get_cached(h)
    if cached:
        return JSONResponse({**cached, "cached": True})

    fname = f"{uuid.uuid4().hex}.jpg"
    fpath = UPLOAD_DIR / fname
    try:
        fpath.write_bytes(raw)
        preprocess(str(fpath))

        result = await run_agent(str(fpath))

        out = {
            "answer": result["answer"],
            "sources": result["sources"],
            "steps": result["steps"]
        }
        set_cached(h, {"answer": out["answer"], "sources": out["sources"]})

        return JSONResponse({**out, "cached": False})

    finally:
        if fpath.exists():
            os.remove(fpath)


@app.post("/analyze/auth")
@limiter.limit("20/minute")
async def analyze_auth(request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):
    raw = await file.read()
    h = get_hash(raw)

    cached = get_cached(h)
    if cached:
        return JSONResponse({**cached, "cached": True})

    fname = f"{uuid.uuid4().hex}.jpg"
    fpath = UPLOAD_DIR / fname
    try:
        fpath.write_bytes(raw)
        preprocess(str(fpath))

        result = await run_agent(str(fpath))

        out = {
            "answer": result["answer"],
            "sources": result["sources"],
            "steps": result["steps"]
        }
        set_cached(h, {"answer": out["answer"], "sources": out["sources"]})

        save_history(user["user_id"], h, out["answer"], out["sources"], result["steps"])

        return JSONResponse({**out, "cached": False})

    finally:
        if fpath.exists():
            os.remove(fpath)


# ============ QUEUE (Celery) ============

@app.post("/analyze/async")
@limiter.limit("10/minute")
async def analyze_async(request: Request, file: UploadFile = File(...)):
    try:
        from services.tasks import analyze_task
    except:
        return JSONResponse({"error": "Celery/Redis ishlamayapti. Oddiy /analyze ishlating."}, 503)

    raw = await file.read()
    h = get_hash(raw)

    cached = get_cached(h)
    if cached:
        return JSONResponse({**cached, "cached": True})

    fname = f"{uuid.uuid4().hex}.jpg"
    fpath = UPLOAD_DIR / fname
    fpath.write_bytes(raw)
    preprocess(str(fpath))

    task = analyze_task.delay(str(fpath), h)
    return {"task_id": task.id, "status": "queued"}


@app.get("/task/{task_id}")
async def get_task(task_id: str):
    try:
        from services.tasks import celery_app
        result = celery_app.AsyncResult(task_id)
        if result.ready():
            return {"status": "done", "result": result.get()}
        return {"status": result.state.lower()}
    except:
        return JSONResponse({"error": "Celery/Redis ishlamayapti"}, 503)


# ============ HISTORY ============

@app.get("/history")
async def history(user=Depends(get_current_user)):
    items = get_history(user["user_id"])
    return {"history": items}


@app.get("/")
async def root():
    return {
        "status": "ok",
        "endpoints": {
            "POST /analyze": "rasm tahlili (bepul, rate limited)",
            "POST /analyze/auth": "rasm tahlili + history (JWT kerak)",
            "POST /analyze/async": "async tahlil (Celery/Redis kerak)",
            "POST /register": "ro'yxatdan o'tish",
            "POST /login": "kirish",
            "GET /history": "tahlil tarixi (JWT kerak)",
            "GET /task/{id}": "async task natijasi",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
