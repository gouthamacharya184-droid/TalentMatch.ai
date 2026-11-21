import subprocess
import time
import json
import urllib.request
import asyncio
import websockets

async def test_ui_interaction():
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

            async def receiver():
                try:
                    async for raw in ws:
                        d = json.loads(raw)
                        if "id" in d:
                            fut = pending.pop(d["id"], None)
                            if fut and not fut.done():
                                fut.set_result(d)
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

            print("\n1. Navigating to http://localhost:5173/resumes/upload ...")
            await send("Page.navigate", {"url": "http://localhost:5173/resumes/upload"})
            await asyncio.sleep(3)

            # Check button exists
            btn_check = await send("Runtime.evaluate", {
                "expression": "Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Demo Resumes'))?.innerText"
            })
            btn_text = btn_check.get("result", {}).get("result", {}).get("value")
            print(f"Found button: '{btn_text}'")

            # Click "Load 15 Demo Resumes"
            print("2. Clicking 'Load 15 Demo Resumes' button in browser...")
            click_res = await send("Runtime.evaluate", {
                "expression": """
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Demo Resumes'));
                if (btn) { btn.click(); 'clicked'; } else { 'not_found'; }
                """
            })
            print("Click result:", click_res.get("result", {}).get("result", {}).get("value"))

            # Wait for sample batch load and parse
            print("3. Waiting 4 seconds for backend to return batch and frontend to update...")
            await asyncio.sleep(4)

            # Inspect page text for completed items
            res_body = await send("Runtime.evaluate", {"expression": "document.body.innerText"})
            body_text = res_body.get("result", {}).get("result", {}).get("value", "")

            # Count queue items
            queue_count = await send("Runtime.evaluate", {
                "expression": "document.querySelectorAll('.truncate').length"
            })
            item_count = queue_count.get("result", {}).get("result", {}).get("value", 0)
            print(f"Queue rendered items count: {item_count}")

            if "Completed" in body_text and "Upload Batch Queue" in body_text:
                print("SUCCESS: Demo resumes loaded and rendered in queue successfully!")
                # Check if "Proceed to AI Matching" button appeared
                match_btn = await send("Runtime.evaluate", {
                    "expression": "Boolean(Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('AI Matching')))"
                })
                print("'Proceed to AI Matching' button visible:", match_btn.get("result", {}).get("result", {}).get("value"))
            else:
                print("Body snippet:")
                print(body_text[:400])

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_ui_interaction())
