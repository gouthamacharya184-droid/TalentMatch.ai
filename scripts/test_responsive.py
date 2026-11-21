import subprocess
import time
import json
import urllib.request
import asyncio
import websockets

VIEWPORTS = [
    ("Mobile (375x667)", 375, 667, 2.0, True),
    ("Tablet (768x1024)", 768, 1024, 2.0, False),
    ("Desktop (1440x900)", 1440, 900, 1.0, False),
]

PAGES = [
    ("/", "Dashboard"),
    ("/resumes/upload", "Resume Upload"),
    ("/jobs", "Jobs"),
    ("/candidates", "Candidates"),
    ("/ranking", "Candidate Ranking"),
]

async def test_responsive():
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

            # Login and seed
            login_req = urllib.request.Request(
                'http://127.0.0.1:8000/api/auth/login',
                data=json.dumps({"email": "recruiter@talentmatch.ai", "password": "Recruiter@123456"}).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(login_req) as l_res:
                auth_data = json.loads(l_res.read())
                token = auth_data["access_token"]
                user = auth_data["user"]

            await send("Page.navigate", {"url": "http://localhost:5173/login"})
            await asyncio.sleep(1)

            set_js = f"""
            localStorage.setItem('access_token', '{token}');
            localStorage.setItem('user', JSON.stringify({json.dumps(user)}));
            """
            await send("Runtime.evaluate", {"expression": set_js})

            print("=" * 65)
            print("Responsive Layout Audit across Mobile, Tablet, and Desktop")
            print("=" * 65)

            for vp_name, w, h, dpr, is_mobile in VIEWPORTS:
                await send("Emulation.setDeviceMetricsOverride", {
                    "width": w,
                    "height": h,
                    "deviceScaleFactor": dpr,
                    "mobile": is_mobile
                })

                print(f"\n--- Viewport: {vp_name} ---")
                for path, name in PAGES:
                    await send("Page.navigate", {"url": f"http://localhost:5173{path}"})
                    await asyncio.sleep(1.2)

                    overflow_check = await send("Runtime.evaluate", {
                        "expression": "document.documentElement.scrollWidth <= window.innerWidth + 2"
                    })
                    no_overflow = overflow_check.get("result", {}).get("result", {}).get("value", False)
                    status = "PASS" if no_overflow else "WARN"
                    print(f"  [{status}] {name:<20} {path:<16} (No horizontal overflow: {no_overflow})")

            print("\nResponsive design verification complete.")

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(test_responsive())
