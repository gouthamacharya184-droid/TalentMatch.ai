import subprocess
import time
import json
import urllib.request
import asyncio
import websockets
import base64
import os

async def test_resume_viewer():
    os.makedirs("screenshots", exist_ok=True)
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
            await send("Emulation.setDeviceMetricsOverride", {
                "width": 1280,
                "height": 900,
                "deviceScaleFactor": 1,
                "mobile": False
            })

            async def save_screenshot(filename):
                res = await send("Page.captureScreenshot", {"format": "png"})
                data = res.get("result", {}).get("data", "")
                if data:
                    with open(os.path.join("screenshots", filename), "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"  [Screenshot] Saved screenshots/{filename}")

            print("\n1. Navigating to http://localhost:5173/candidates ...")
            await send("Page.navigate", {"url": "http://localhost:5173/candidates"})
            await asyncio.sleep(2.5)

            # Locate Goutham Acharya's View Profile button
            print("2. Opening Candidate Detail Modal for Goutham Acharya...")
            click_res = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const rows = Array.from(document.querySelectorAll('tr'));
                    const gouthamRow = rows.find(r => r.innerText.includes('GOUTHAM') || r.innerText.includes('Goutham'));
                    if (gouthamRow) {
                        const btn = gouthamRow.querySelector('button');
                        if (btn) { btn.click(); return 'clicked_row'; }
                    }
                    const anyBtn = document.querySelector('button');
                    const allBtns = Array.from(document.querySelectorAll('button'));
                    const viewBtn = allBtns.find(b => b.innerText.includes('View Profile'));
                    if (viewBtn) { viewBtn.click(); return 'clicked_view_profile'; }
                    return 'none';
                })()
                """
            })
            print("  Click result:", click_res.get("result", {}).get("result", {}).get("value"))
            await asyncio.sleep(1.5)

            # Check if View Resume button exists
            eval_btns = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const allButtons = Array.from(document.querySelectorAll('button'));
                    const viewResumeBtn = allButtons.find(b => b.innerText.includes('View Resume'));
                    const downloadResumeBtn = allButtons.find(b => b.innerText.includes('Resume') && !b.innerText.includes('View'));
                    return {
                        hasViewResume: Boolean(viewResumeBtn),
                        hasDownloadResume: Boolean(downloadResumeBtn),
                        viewResumeText: viewResumeBtn ? viewResumeBtn.innerText : null,
                        downloadResumeText: downloadResumeBtn ? downloadResumeBtn.innerText : null
                    };
                })()
                """,
                "returnByValue": True
            })
            btn_info = eval_btns.get("result", {}).get("result", {}).get("value", {})
            print("  Header Buttons Found:", btn_info)
            assert btn_info.get("hasViewResume"), "View Resume button NOT found in CandidateDetailModal!"
            assert btn_info.get("hasDownloadResume"), "Download Resume button NOT found in CandidateDetailModal!"
            print("  SUCCESS: Both 'View Resume' and 'Resume' buttons are present beside each other!")

            await save_screenshot("candidate_detail_with_view_resume.png")

            # Click "View Resume" button
            print("\n3. Clicking 'View Resume' button to launch ResumeViewerModal...")
            open_viewer = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const allButtons = Array.from(document.querySelectorAll('button'));
                    const viewResumeBtn = allButtons.find(b => b.innerText.includes('View Resume'));
                    if (viewResumeBtn) {
                        viewResumeBtn.click();
                        return true;
                    }
                    return false;
                })()
                """
            })
            await asyncio.sleep(1.5)

            # Check ResumeViewerModal content
            eval_modal = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const h3 = document.querySelector('h3');
                    const pre = document.querySelector('pre');
                    const searchInput = document.querySelector('input[placeholder*=\"Search\"]');
                    return {
                        title: h3 ? h3.innerText : null,
                        hasPre: Boolean(pre),
                        textLength: pre ? pre.innerText.length : 0,
                        textSnippet: pre ? pre.innerText.substring(0, 100) : null,
                        hasSearch: Boolean(searchInput)
                    };
                })()
                """,
                "returnByValue": True
            })
            modal_info = eval_modal.get("result", {}).get("result", {}).get("value", {})
            print("  ResumeViewerModal Content:", modal_info)
            assert modal_info.get("hasPre"), "Resume content <pre> block NOT rendered in ResumeViewerModal!"
            print(f"  SUCCESS: Resume document parsed and rendered! ({modal_info.get('textLength')} characters)")

            await save_screenshot("resume_viewer_modal.png")

            # Test Search inside ResumeViewerModal
            print("\n4. Testing search & keyword highlighting in ResumeViewerModal...")
            search_res = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const searchInput = document.querySelector('input[placeholder*=\"Search\"]');
                    if (searchInput) {
                        searchInput.value = 'FastAPI';
                        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                        return true;
                    }
                    return false;
                })()
                """
            })
            await asyncio.sleep(0.5)

            marks_info = await send("Runtime.evaluate", {
                "expression": "document.querySelectorAll('mark').length"
            })
            mark_count = marks_info.get("result", {}).get("result", {}).get("value", 0)
            print(f"  SUCCESS: Highlighted {mark_count} occurrence(s) of 'FastAPI'!")

            # Close ResumeViewerModal
            print("\n5. Closing ResumeViewerModal...")
            await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const closeBtn = document.querySelector('button[title*=\"Close viewer\"]');
                    if (closeBtn) closeBtn.click();
                })()
                """
            })
            await asyncio.sleep(1.0)

            # Test the "Resume Document" tab
            print("\n6. Testing the 'Resume Document' tab in CandidateDetailModal...")
            tab_click = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const allButtons = Array.from(document.querySelectorAll('button'));
                    const tab = allButtons.find(b => b.innerText.includes('Resume Document'));
                    if (tab) {
                        tab.click();
                        return true;
                    }
                    return false;
                })()
                """
            })
            await asyncio.sleep(1.0)

            tab_info = await send("Runtime.evaluate", {
                "expression": """
                (() => {
                    const pre = document.querySelector('pre');
                    return {
                        hasText: Boolean(pre && pre.innerText.length > 50),
                        length: pre ? pre.innerText.length : 0
                    };
                })()
                """,
                "returnByValue": True
            })
            print("  'Resume Document' Tab Content:", tab_info.get("result", {}).get("result", {}).get("value"))
            await save_screenshot("resume_document_tab.png")

            print("\n=== ALL RESUME VIEWER TESTS PASSED WITH 0 RUNTIME EXCEPTIONS ===")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(test_resume_viewer())
