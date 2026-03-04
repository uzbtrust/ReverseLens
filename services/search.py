from PicImageSearch import Network, Tineye, Yandex, Bing


async def search_tineye(filepath):
    results = []
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
    return results


async def search_yandex(filepath):
    results = []
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
    return results


async def search_bing(filepath):
    results = []
    async with Network(timeout=15) as client:
        bing = Bing(client=client)
        resp = await bing.search(file=filepath)
        if resp:
            if resp.best_guess:
                results.append({
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
    return results


async def search_img(filepath):
    results = []

    try:
        results = await search_tineye(filepath)
    except:
        pass

    if len(results) < 3:
        try:
            results.extend(await search_yandex(filepath))
        except:
            pass

    if len(results) < 3:
        try:
            results.extend(await search_bing(filepath))
        except:
            pass

    return results[:10]
