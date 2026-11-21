import subprocess
import time
import json
import urllib.request
import asyncio
import websockets

async def test_pending_flow():
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

            # 1. Navigate to /resumes/upload
            await send("Page.navigate", {"url": "http://localhost:5173/resumes/upload"})
            await asyncio.sleep(2)

            # 2. Simulate dropping a file by evaluating JS that adds an item
            sim_js = """
            const file = new File(['Maria Gomez\\nEmail: maria@example.com\\nSkills: Python, FastAPI\\nExperience: 4 years'], 'Maria_Gomez_Resume.txt', { type: 'text/plain' });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            const input = document.querySelector('input[type="file"]');
            input.files = dataTransfer.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
            """
            await send("Runtime.evaluate", {"expression": sim_js})
            await asyncio.sleep(1)

            res_body = await send("Runtime.evaluate", {"expression": "document.body.innerText"})
            body_text = res_body.get("result", {}).get("result", {}).get("value", "")
            print("--- Page text after adding 1 file ---")
            for line in body_text.split("\n"):
                if any(k in line for k in ["Batch Queue", "Pending", "Process", "Start Batch"]):
                    print("  >", line.strip())

            # 3. Now click the individual "Process" button or "Start Batch Extraction"
            print("\nClicking individual 'Process' button for the pending file...")
            click_res = await send("Runtime.evaluate", {
                "expression": """
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.trim() === 'Process');
                if (btn) { btn.click(); 'clicked'; } else { 'not found'; }
                """
            })
            print("Click result:", click_res.get("result", {}).get("result", {}).get("value"))

            await asyncio.sleep(3)

            res_body2 = await send("Runtime.evaluate", {"expression": "document.body.innerText"})
            body_text2 = res_body2.get("result", {}).get("result", {}).get("value", "")
            print("\n--- Page text after processing ---")
            for line in body_text2.split("\n"):
                if any(k in line for k in ["Completed", "Candidate indexed", "Batch", "Queue"]):
                    print("  >", line.strip())

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_pending_flow())
