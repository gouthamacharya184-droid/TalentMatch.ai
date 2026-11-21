import asyncio, websockets, json, subprocess, urllib.request, base64

async def test_modal():
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([chrome_path, '--headless=new', '--remote-debugging-port=9222', '--disable-gpu', 'about:blank'])
    await asyncio.sleep(2)
    req = urllib.request.urlopen('http://127.0.0.1:9222/json')
    tabs = json.loads(req.read())
    ws_url = tabs[0]['webSocketDebuggerUrl']
    async with websockets.connect(ws_url) as ws:
        msg_id = 0
        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {'id': msg_id, 'method': method}
            if params: payload['params'] = params
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get('id') == msg_id: return resp

        await send('Page.enable')
        await send('Runtime.enable')
        await send('Emulation.setDeviceMetricsOverride', {'width': 1280, 'height': 850, 'deviceScaleFactor': 1, 'mobile': False})

        print("1. Loading /candidates ...")
        await send('Page.navigate', {'url': 'http://localhost:5173/candidates'})
        await asyncio.sleep(2.5)

        print("2. Clicking 'View Profile' on Goutham Acharya...")
        await send('Runtime.evaluate', {
            'expression': """
            (() => {
                const rows = Array.from(document.querySelectorAll('tr'));
                const gRow = rows.find(r => r.innerText.includes('GOUTHAM') || r.innerText.includes('Goutham'));
                if (gRow) {
                    const btn = gRow.querySelector('button');
                    if (btn) btn.click();
                }
            })()
            """
        })
        await asyncio.sleep(1.5)

        # Check #view-resume-btn exists
        btn_chk = await send('Runtime.evaluate', {
            'expression': "Boolean(document.getElementById('view-resume-btn'))"
        })
        print("view-resume-btn exists in DOM:", btn_chk.get('result', {}).get('result', {}).get('value'))

        # Take screenshot of Candidate Detail Modal
        snap1 = await send('Page.captureScreenshot', {'format': 'png'})
        with open('screenshots/candidate_detail_view_resume_btn.png', 'wb') as f:
            f.write(base64.b64decode(snap1['result']['data']))
        print("Saved screenshots/candidate_detail_view_resume_btn.png")

        # Click #view-resume-btn
        print("3. Clicking #view-resume-btn ...")
        await send('Runtime.evaluate', {
            'expression': "document.getElementById('view-resume-btn').click()"
        })
        await asyncio.sleep(1.5)

        # Check #resume-viewer-modal exists
        modal_chk = await send('Runtime.evaluate', {
            'expression': "Boolean(document.getElementById('resume-viewer-modal'))"
        })
        print("resume-viewer-modal exists in DOM:", modal_chk.get('result', {}).get('result', {}).get('value'))

        modal_text = await send('Runtime.evaluate', {
            'expression': "document.getElementById('resume-viewer-modal') ? document.getElementById('resume-viewer-modal').innerText.substring(0, 300) : 'none'"
        })
        print("Modal text snippet:\n", modal_text.get('result', {}).get('result', {}).get('value'))

        # Take screenshot of Resume Viewer Modal
        snap2 = await send('Page.captureScreenshot', {'format': 'png'})
        with open('screenshots/resume_viewer_fullscreen.png', 'wb') as f:
            f.write(base64.b64decode(snap2['result']['data']))
        print("Saved screenshots/resume_viewer_fullscreen.png")

        # Test Resume Document Tab
        print("4. Testing 'Resume Document' tab inside Candidate Detail Modal...")
        await send('Runtime.evaluate', {
            'expression': """
            (() => {
                const closeBtn = document.querySelector('#resume-viewer-modal button[title*=\"Close\"]');
                if (closeBtn) closeBtn.click();
            })()
            """
        })
        await asyncio.sleep(1.0)

        await send('Runtime.evaluate', {
            'expression': """
            (() => {
                const allButtons = Array.from(document.querySelectorAll('button'));
                const tab = allButtons.find(b => b.innerText.includes('Resume Document'));
                if (tab) tab.click();
            })()
            """
        })
        await asyncio.sleep(1.0)

        tab_snap = await send('Page.captureScreenshot', {'format': 'png'})
        with open('screenshots/candidate_resume_tab.png', 'wb') as f:
            f.write(base64.b64decode(tab_snap['result']['data']))
        print("Saved screenshots/candidate_resume_tab.png")

    proc.kill()

if __name__ == '__main__':
    asyncio.run(test_modal())
