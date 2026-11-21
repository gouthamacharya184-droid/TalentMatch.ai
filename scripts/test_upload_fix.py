import subprocess
import time
import json
import urllib.request
import asyncio
import websockets

async def test_upload_fix():
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
            exceptions = []

            async def receiver():
                try:
                    async for raw in ws:
                        d = json.loads(raw)
                        if "id" in d:
                            fut = pending.pop(d["id"], None)
                            if fut and not fut.done():
                                fut.set_result(d)
                        else:
                            method = d.get("method")
                            if method == "Runtime.exceptionThrown":
                                exceptions.append(d)
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
            await asyncio.sleep(2)

            # Check if ErrorBoundary triggered
            error_boundary_active = await send("Runtime.evaluate", {
                "expression": "Boolean(document.querySelector('h2')?.innerText.includes('Module Interface Error'))"
            })
            print("ErrorBoundary active on initial load:", error_boundary_active.get("result", {}).get("result", {}).get("value"))

            # Add a real PDF / TXT file
            print("2. Simulating file selection...")
            sim_js = """
            const fileContent = `Sophia Williams
Email: sophia.williams.dev@example.com
Phone: +1 555 456 7890
Location: San Francisco, CA

EXPERIENCE
Senior Python Architect | NextGen Cloud (2021 - Present) - 3 years
- Built high-throughput distributed systems with Python, FastAPI, and Redis.
- Implemented real-time processing pipelines.

SKILLS
Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, React, TypeScript
`;
            const file = new File([fileContent], 'Sophia_Williams_Lead.txt', { type: 'text/plain' });
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            const input = document.querySelector('input[type="file"]');
            input.files = dataTransfer.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
            """
            await send("Runtime.evaluate", {"expression": sim_js})
            await asyncio.sleep(1)

            # Click "Start Batch Extraction"
            print("3. Clicking 'Start Batch Extraction'...")
            click_btn = await send("Runtime.evaluate", {
                "expression": """
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Start Batch Extraction'));
                if (btn) { btn.click(); 'clicked'; } else { 'not found'; }
                """
            })
            print("Click result:", click_btn.get("result", {}).get("result", {}).get("value"))

            # Wait for upload and processing
            print("4. Waiting 4 seconds for upload and NLP extraction...")
            await asyncio.sleep(4)

            # Check page status
            res_body = await send("Runtime.evaluate", {"expression": "document.body.innerText"})
            body_text = res_body.get("result", {}).get("result", {}).get("value", "")

            # Check for Module Interface Error
            has_module_error = "Module Interface Error" in body_text
            print(f"Has Module Interface Error: {has_module_error}")
            print(f"Uncaught runtime exceptions: {len(exceptions)}")

            if "Completed" in body_text:
                print("SUCCESS: File uploaded, processed, and marked Completed!")
                if "Candidate indexed" in body_text:
                    print("SUCCESS: Candidate indexed badge verified!")
            else:
                print("Body text snippet:")
                print(body_text[:500])

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_upload_fix())
