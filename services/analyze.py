import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"


async def ask_llm(prompt, temp=0.3):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temp}
            })
            data = resp.json()
            return data.get("response", "").strip()
    except httpx.ConnectError:
        return None
    except:
        return None


async def make_answer(search_results):
    if not search_results:
        return "Hech narsa topilmadi"

    texts = []
    for r in search_results:
        line = r["title"]
        if r.get("snippet"):
            line += f" - {r['snippet']}"
        texts.append(line)

    joined = "\n".join(texts)

    prompt = f"""Quyida internetdan teskari rasm qidiruv orqali topilgan natijalar bor.
Bu matnlarga asoslanib, rasmda NIMA tasvirlangan - bitta aniq va qisqa gap bilan javob ber.
Faqat o'zbekcha javob ber. Ortiqcha gap keremas, faqat rasmni tasvirla.

Natijalar:
{joined}

Javob:"""

    answer = await ask_llm(prompt)
    if answer:
        return answer

    return f"Taxminiy: {search_results[0]['title']}"
