import json
import hashlib
from pathlib import Path

CACHE_FILE = Path(__file__).parent.parent / "cache.json"

def get_hash(img_bytes):
    return hashlib.md5(img_bytes).hexdigest()

def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except:
            return {}
    return {}

def save_cache(data):
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def get_cached(h):
    c = load_cache()
    return c.get(h)

def set_cached(h, result):
    c = load_cache()
    c[h] = result
    save_cache(c)
