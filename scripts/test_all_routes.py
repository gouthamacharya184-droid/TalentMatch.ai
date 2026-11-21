import subprocess
import time
import json
import urllib.request
import asyncio
import websockets

ROUTES = [
    ("/", "Dashboard"),
    ("/jobs", "Jobs"),
    ("/resumes/upload", "Resume Upload"),
    ("/matching", "AI Matching"),
    ("/candidates", "Candidates"),
    ("/ranking", "Candidate Ranking"),
    ("/compare", "Compare Candidates"),
    ("/shortlist", "Shortlisted"),
    ("/analytics", "Analytics"),
    ("/history", "Analysis History"),
    ("/profile", "Profile"),
    ("/settings", "Settings"),
    ("/security", "Security"),
    ("/login", "Login"),
    ("/register", "Register"),
]

async def audit_all_routes():
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

    results = []

    try:
        req = urllib.request.urlopen('http://127.0.0.1:9222/json')
        tabs = json.loads(req.read())
        page_tab = next(t for t in tabs if t.get('type') == 'page')
        ws_url = page_tab['webSocketDebuggerUrl']

        async with websockets.connect(ws_url) as ws:
            msg_id = 0
            pending = {}
            uncaught_exceptions = []

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
                                uncaught_exceptions.append(d)
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

            # Seed localStorage with active recruiter session
            await send("Page.navigate", {"url": "http://localhost:5173/login"})
            await asyncio.sleep(1.5)

            # Get token
            login_req = urllib.request.Request(
                'http://127.0.0.1:8000/api/auth/login',
                data=json.dumps({"email": "recruiter@talentmatch.ai", "password": "Recruiter@123456"}).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(login_req) as l_res:
                auth_data = json.loads(l_res.read())
                token = auth_data["access_token"]
                user = auth_data["user"]

            set_js = f"""
            localStorage.setItem('access_token', '{token}');
            localStorage.setItem('user', JSON.stringify({json.dumps(user)}));
            """
            await send("Runtime.evaluate", {"expression": set_js})

            print("=" * 65)
            print("TalentMatch AI — Full Frontend Route Audit (Headless Chrome)")
            print("=" * 65)

            for path, name in ROUTES:
                url = f"http://localhost:5173{path}"
                uncaught_exceptions.clear()
                await send("Page.navigate", {"url": url})
                await asyncio.sleep(1.5)

                res_url = await send("Runtime.evaluate", {"expression": "window.location.href"})
                current_url = res_url.get("result", {}).get("result", {}).get("value", "")

                res_root = await send("Runtime.evaluate", {"expression": "document.getElementById('root')?.innerHTML.length || 0"})
                root_len = res_root.get("result", {}).get("result", {}).get("value", 0)

                res_text = await send("Runtime.evaluate", {"expression": "document.body.innerText"})
                body_text = res_text.get("result", {}).get("result", {}).get("value", "")

                is_blank = root_len < 50 or len(body_text.strip()) == 0
                has_exception = len(uncaught_exceptions) > 0

                status = "FAIL" if (is_blank or has_exception) else "PASS"
                details = f"DOM={root_len} chars | text_preview={repr(body_text[:40].strip())}"
                if has_exception:
                    details += f" | EXCEPTION={uncaught_exceptions[0]}"

                print(f"[{status}] {name:<22} {path:<20} -> {details}")
                results.append({"route": path, "name": name, "status": status, "root_len": root_len})

            print("=" * 65)
            passed = sum(1 for r in results if r["status"] == "PASS")
            print(f"ROUTE AUDIT RESULT: {passed}/{len(results)} Routes PASSED")
            print("=" * 65)

    finally:
        proc.terminate()

if __name__ == "__main__":
    asyncio.run(audit_all_routes())
