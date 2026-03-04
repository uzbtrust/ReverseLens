import httpx
from services.tools import TOOL_SCHEMAS, TOOL_FUNCTIONS, fmt_result

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1"
MAX_TURNS = 8

SYSTEM_PROMPT = """Siz ReverseLens — teskari rasm qidiruv agentisiz.

Sizga rasm fayli beriladi. Vazifangiz: mavjud tool'lardan foydalanib, rasmda nima tasvirlangan — aniqlab bering.

Sizning tool'laringiz:
- search_tineye: TinEye qidiruv (aniq, lekin kam natija berishi mumkin)
- search_yandex: Yandex qidiruv (ko'p natija)
- search_bing: Bing qidiruv (best guess + natijalar)
- generate_description: Natijalar asosida tavsif yaratish

Ishlash tartibi:
1. Avval bitta qidiruv engine tanlang va chaqiring
2. Natijalarni ko'ring — yetarlimi yoki boshqa engine kerakmi?
3. Yetarli natija bo'lsa (kamida 3 ta) — generate_description ni chaqiring
4. Agar engine hech narsa topmasa yoki xato bersa — boshqa engine sinab ko'ring
5. Oxirida foydalanuvchiga yakuniy javobni O'ZBEKCHADA yozing

Muhim qoidalar:
- Har qadamda FAQAT BITTA tool chaqiring
- Barcha engine sinalgach ham natija bo'lmasa, shuni ayting
- Yakuniy javob QISQA va ANIQ bo'lsin (1-2 gap)
- Tool chaqirmasdan to'g'ridan-to'g'ri javob yozsangiz, bu yakuniy javob hisoblanadi"""


class ReactAgent:
    def __init__(self, filepath):
        self.filepath = filepath
        self.messages = []
        self.steps = []
        self.all_results = []
        self.turn = 0

    async def run(self):
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Bu rasmni aniqlang. Fayl yo'li: {self.filepath}"}
        ]

        while self.turn < MAX_TURNS:
            self.turn += 1

            self.steps.append({"action": "llm_think", "turn": self.turn, "status": "started"})
            resp = await self._call_ollama()

            if resp is None:
                self.steps[-1]["status"] = "failed"
                return self._fallback()

            msg = resp.get("message", {})
            self.steps[-1]["status"] = "done"

            tool_calls = msg.get("tool_calls")

            if tool_calls:
                self.messages.append(msg)

                for tc in tool_calls:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    args = fn.get("arguments", {})

                    self.steps.append({
                        "action": "tool_call",
                        "tool": name,
                        "args": args,
                        "turn": self.turn,
                        "status": "started"
                    })

                    result = await self._exec_tool(name, args)
                    self.steps[-1]["status"] = "done"
                    self.steps[-1]["result_preview"] = str(result)[:200]

                    if name.startswith("search_") and isinstance(result, list):
                        self.steps[-1]["count"] = len(result)
                        self.all_results.extend(result)

                    self.messages.append({
                        "role": "tool",
                        "content": fmt_result(result)
                    })
            else:
                answer = msg.get("content", "").strip()
                self.steps.append({"action": "final_answer", "turn": self.turn, "status": "done"})
                self.messages.append(msg)
                return self._build(answer)

        self.steps.append({"action": "max_turns", "turn": self.turn, "status": "done"})
        return await self._force_answer()

    async def _call_ollama(self):
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                r = await client.post(OLLAMA_URL, json={
                    "model": MODEL,
                    "messages": self.messages,
                    "tools": TOOL_SCHEMAS,
                    "stream": False,
                    "options": {"temperature": 0.3}
                })
                return r.json()
        except:
            return None

    async def _exec_tool(self, name, args):
        func = TOOL_FUNCTIONS.get(name)
        if not func:
            return f"Xato: '{name}' tool topilmadi"
        try:
            return await func(**args)
        except Exception as e:
            return f"Tool xatosi ({name}): {str(e)}"

    def _build(self, answer):
        seen = set()
        sources = []
        for r in self.all_results:
            url = r.get("url", "")
            if url and url not in seen:
                seen.add(url)
                sources.append({"title": r["title"], "url": url})
        return {
            "answer": answer or "Rasmni aniqlab bo'lmadi",
            "sources": sources[:5],
            "steps": self.steps
        }

    def _fallback(self):
        return {
            "answer": "Ollama serveriga ulanib bo'lmadi",
            "sources": [],
            "steps": self.steps
        }

    async def _force_answer(self):
        lines = []
        for r in self.all_results[:10]:
            l = r["title"]
            if r.get("snippet"):
                l += f" - {r['snippet']}"
            lines.append(l)

        self.messages.append({
            "role": "user",
            "content": "Yetarli qidirdingiz. Toplangan natijalar asosida rasmda nima bor — qisqa javob bering.\n\nNatijalar:\n" + "\n".join(lines)
        })

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(OLLAMA_URL, json={
                    "model": MODEL,
                    "messages": self.messages,
                    "stream": False,
                    "options": {"temperature": 0.3}
                })
                content = r.json().get("message", {}).get("content", "").strip()
                return self._build(content)
        except:
            if self.all_results:
                return self._build(f"Taxminiy: {self.all_results[0]['title']}")
            return self._build("Rasmni aniqlab bo'lmadi")
