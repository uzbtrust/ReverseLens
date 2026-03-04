import asyncio
from celery import Celery

celery_app = Celery(
    "reverselens",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600


@celery_app.task(bind=True, name="analyze_image")
def analyze_task(self, filepath, img_hash, user_id=None):
    from services.agent import run_agent
    from services.preprocess import preprocess
    from utils.cache import get_cached, set_cached
    from utils.db import save_history

    cached = get_cached(img_hash)
    if cached:
        return {**cached, "cached": True}

    preprocess(filepath)

    result = asyncio.run(run_agent(filepath))

    out = {
        "answer": result["answer"],
        "sources": result["sources"],
        "steps": result["steps"]
    }
    set_cached(img_hash, {"answer": out["answer"], "sources": out["sources"]})

    if user_id:
        save_history(user_id, img_hash, out["answer"], out["sources"], out["steps"])

    return {**out, "cached": False}
