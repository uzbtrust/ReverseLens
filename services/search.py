from PicImageSearch import Network, Tineye, Yandex, Bing


async def search_img(filepath):
    results = []

    # tineye eng ishonchli hozircha
    try:
        async with Network(timeout=20) as client:
            te = Tineye(client=client)
            resp = await te.search(file=filepath)
            if resp and resp.raw:
                for item in resp.raw[:10]:
                    title = item.title or ""
                    if not title and item.image_url:
                        title = item.image_url.split("/")[-1]
                    if item.url:
                        results.append({
                            "title": title or item.url.split("/")[2],
                            "url": item.url,
                            "snippet": ""
                        })
    except:
        pass

    # kam natija bo'lsa yandex sinab ko'ramiz
    if len(results) < 3:
        try:
            async with Network(timeout=15) as client:
                yandex = Yandex(client=client)
                resp = await yandex.search(file=filepath)
                if resp and resp.raw:
                    for item in resp.raw[:10]:
                        if item.title and item.url:
                            results.append({
                                "title": item.title,
                                "url": item.url,
                                "snippet": item.content or ""
                            })
        except:
            pass

    # hali kam bo'lsa - bing
    if len(results) < 3:
        try:
            async with Network(timeout=15) as client:
                bing = Bing(client=client)
                resp = await bing.search(file=filepath)
                if resp:
                    if resp.best_guess:
                        results.insert(0, {
                            "title": resp.best_guess,
                            "url": "",
                            "snippet": "bing best guess"
                        })
                    if resp.pages_including:
                        for item in resp.pages_including[:10]:
                            if item.name and item.url:
                                results.append({
                                    "title": item.name,
                                    "url": item.url,
                                    "snippet": ""
                                })
        except:
            pass

    return results[:10]
