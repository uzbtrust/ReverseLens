import json
from services.search import search_tineye, search_yandex, search_bing
from services.analyze import make_answer

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_tineye",
            "description": "TinEye orqali teskari rasm qidiruv. Rasmning asl manbalarini topadi. Aniq natija beradi lekin kam topishi mumkin.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Qidiriladigan rasm faylining to'liq yo'li"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_yandex",
            "description": "Yandex orqali teskari rasm qidiruv. Ko'proq natija beradi, ayniqsa taniqli rasmlar uchun yaxshi ishlaydi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Qidiriladigan rasm faylining to'liq yo'li"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_bing",
            "description": "Bing orqali teskari rasm qidiruv. 'Best guess' taxminini ham beradi. Boshqa engine'lar kam topganda foydali.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Qidiriladigan rasm faylining to'liq yo'li"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_description",
            "description": "Toplangan qidiruv natijalariga asoslanib rasmning tavsifini yaratadi. Kamida 3 ta natija bo'lganda chaqiring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "results_text": {
                        "type": "string",
                        "description": "Barcha qidiruv natijalarining sarlavhalari, har biri yangi qatorda"
                    }
                },
                "required": ["results_text"]
            }
        }
    }
]


async def _gen_description(results_text):
    lines = results_text.strip().split("\n")
    results = []
    for line in lines:
        line = line.strip()
        if line:
            results.append({"title": line, "url": "", "snippet": ""})
    if not results:
        return "Natijalar bo'sh"
    return await make_answer(results)


TOOL_FUNCTIONS = {
    "search_tineye": search_tineye,
    "search_yandex": search_yandex,
    "search_bing": search_bing,
    "generate_description": _gen_description,
}


def fmt_result(result):
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False)
