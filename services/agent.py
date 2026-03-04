import httpx
from services.search import search_tineye, search_yandex, search_bing
from services.analyze import make_answer, ask_llm

ENGINES = [
    ("tineye", search_tineye),
    ("yandex", search_yandex),
    ("bing", search_bing),
]


async def run_agent(filepath):
    steps = []
    all_results = []

    # step 1: birinchi engine bilan qidirish
    for name, fn in ENGINES:
        steps.append({"action": "search", "engine": name, "status": "started"})
        try:
            res = await fn(filepath)
            steps[-1]["status"] = "done"
            steps[-1]["count"] = len(res)
            all_results.extend(res)
        except:
            steps[-1]["status"] = "failed"

        # agent qaror qiladi: yetarli natija bormi?
        if len(all_results) >= 5:
            break

    if not all_results:
        steps.append({"action": "decide", "result": "no results from any engine"})
        return {
            "answer": "Hech qanday qidiruv natijasi topilmadi",
            "sources": [],
            "steps": steps
        }

    # step 2: natijalar sifatini LLM bilan baholash
    steps.append({"action": "evaluate", "status": "started"})
    eval_prompt = f"""Quyidagi qidiruv natijalari rasmni aniqlash uchun yetarlimi?
Natijalar: {[r['title'] for r in all_results[:8]]}
Faqat "ha" yoki "yoq" deb javob ber."""

    eval_result = await ask_llm(eval_prompt)
    is_enough = "ha" in eval_result.lower() if eval_result else True
    steps[-1]["status"] = "done"
    steps[-1]["enough"] = is_enough

    # step 3: yetarli emas bo'lsa qo'shimcha engine'larni sinab ko'rish
    if not is_enough and len(all_results) < 3:
        for name, fn in ENGINES:
            already = any(s.get("engine") == name for s in steps if s["action"] == "search")
            if already:
                continue
            steps.append({"action": "search_extra", "engine": name, "status": "started"})
            try:
                res = await fn(filepath)
                steps[-1]["status"] = "done"
                steps[-1]["count"] = len(res)
                all_results.extend(res)
            except:
                steps[-1]["status"] = "failed"

    # step 4: javob generatsiya qilish
    steps.append({"action": "generate_answer", "status": "started"})
    unique = []
    seen = set()
    for r in all_results:
        key = r["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    unique = unique[:10]

    answer = await make_answer(unique)
    steps[-1]["status"] = "done"

    # step 5: javob sifatini tekshirish
    steps.append({"action": "check_quality", "status": "started"})
    check_prompt = f"""Bu javob rasmni yaxshi tasvirlayaptimi?
Javob: "{answer}"
Agar javob juda qisqa, noaniq yoki mantiqsiz bo'lsa "yomon" de, aks holda "yaxshi" de."""

    quality = await ask_llm(check_prompt)
    is_good = "yaxshi" in quality.lower() if quality else True
    steps[-1]["status"] = "done"
    steps[-1]["quality"] = "good" if is_good else "poor"

    # yomon bo'lsa qayta generatsiya
    if not is_good and unique:
        steps.append({"action": "regenerate", "status": "started"})
        answer = await make_answer(unique)
        steps[-1]["status"] = "done"

    sources = [{"title": r["title"], "url": r["url"]} for r in unique if r["url"]][:5]

    return {
        "answer": answer,
        "sources": sources,
        "steps": steps
    }
