import subprocess
import time
import json
import urllib.request
import asyncio
import websockets

async def test_states():
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([
        chrome_path,
        '--headless=new',
        '--remote-debugging-port=9222',
        '--disable-gpu',
        '--no-sandbox',
        'about:blank'
    ])
    await asyncio.sleep(2)

    try:
        req = urllib.request.urlopen('http://127.0.0.1:9222/json')
        tabs = json.loads(req.read())
        page_tab = next(t for t in tabs if t.get('type') == 'page')
        ws_url = page_tab['webSocketDebuggerUrl']

        async with websockets.connect(ws_url) as ws:
            msg_id = 0
            pending = {}
            events = []

            async def receiver():
                try:
                    async for raw in ws:
                        d = json.loads(raw)
                        if "id" in d:
                            fut = pending.pop(d["id"], None)
                            if fut and not fut.done():
                                fut.set_result(d)
                        else:
                            events.append(d)
                except Exception:
                    pass

            asyncio.create_task(receiver())

            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                fut = asyncio.get_running_loop().create_future()
                pending[msg_id] = fut
                payload = {"id": msg_id, "method": method}
                if params:
                    payload["params"] = params
                await ws.send(json.dumps(payload))
                return await fut

            await send("Page.enable")
            await send("Runtime.enable")

            # State 1: Clean slate (no localStorage)
            print("--- State 1: Fresh browser visit to http://localhost:5173/resumes/upload ---")
            await send("Page.navigate", {"url": "http://localhost:5173/resumes/upload"})
            await asyncio.sleep(2)
            res_url = await send("Runtime.evaluate", {"expression": "window.location.href"})
            res_body = await send("Runtime.evaluate", {"expression": "document.body.innerText"})
            res_html = await send("Runtime.evaluate", {"expression": "document.getElementById('root')?.innerHTML"})
            print("URL:", res_url.get("result", {}).get("result", {}).get("value"))
            print("Body text snippet:", repr(res_body.get("result", {}).get("result", {}).get("value")[:200]))
            print("Root HTML length:", len(res_html.get("result", {}).get("result", {}).get("value") or ""))

            # State 2: Invalid/garbage token in localStorage
            print("\n--- State 2: Stale token in localStorage ---")
            await send("Runtime.evaluate", {"expression": "localStorage.setItem('access_token', 'invalid_expired_token_abc');"})
            await send("Page.navigate", {"url": "http://localhost:5173/resumes/upload"})
            await asyncio.sleep(2)
            res_url = await send("Runtime.evaluate", {"expression": "window.location.href"})
            res_body = await send("Runtime.evaluate", {"expression": "document.body.innerText"})
            res_html = await send("Runtime.evaluate", {"expression": "document.getElementById('root')?.innerHTML"})
            print("URL:", res_url.get("result", {}).get("result", {}).get("value"))
            print("Body text snippet:", repr(res_body.get("result", {}).get("result", {}).get("value")[:200]))
            print("Root HTML length:", len(res_html.get("result", {}).get("result", {}).get("value") or ""))

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_states())
