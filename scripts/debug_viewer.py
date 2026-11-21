import asyncio, websockets, json, subprocess, urllib.request

async def test_error():
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    proc = subprocess.Popen([chrome_path, '--headless=new', '--remote-debugging-port=9222', '--disable-gpu', 'about:blank'])
    await asyncio.sleep(2)
    req = urllib.request.urlopen('http://127.0.0.1:9222/json')
    tabs = json.loads(req.read())
    ws_url = tabs[0]['webSocketDebuggerUrl']
    async with websockets.connect(ws_url) as ws:
        msg_id = 0
        exceptions = []
        async def receiver():
            try:
                async for raw in ws:
                    d = json.loads(raw)
                    if "id" in d:
                        fut = pending.pop(d["id"], None)
                        if fut and not fut.done(): fut.set_result(d)
                    elif d.get("method") == "Runtime.exceptionThrown":
                        exceptions.append(d)
            except Exception: pass

        pending = {}
        asyncio.create_task(receiver())

        async def send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            fut = asyncio.get_running_loop().create_future()
            pending[msg_id] = fut
            payload = {'id': msg_id, 'method': method}
            if params: payload['params'] = params
            await ws.send(json.dumps(payload))
            return await fut

        await send('Page.enable')
        await send('Runtime.enable')

        await send('Page.navigate', {'url': 'http://localhost:5173/candidates'})
        await asyncio.sleep(2)

        # Open View Profile
        await send('Runtime.evaluate', {
            'expression': """
            const btns = Array.from(document.querySelectorAll('button'));
            const vp = btns.find(b => b.innerText.includes('View Profile'));
            if (vp) vp.click();
            """
        })
        await asyncio.sleep(1)

        # Open View Resume
        await send('Runtime.evaluate', {
            'expression': """
            const btns = Array.from(document.querySelectorAll('button'));
            const vr = btns.find(b => b.innerText.includes('View Resume'));
            if (vr) vr.click();
            """
        })
        await asyncio.sleep(1)

        body_text = await send('Runtime.evaluate', {'expression': 'document.body.innerText'})
        print("=== BODY TEXT ===")
        print(body_text.get('result', {}).get('result', {}).get('value'))

        print("\n=== RUNTIME EXCEPTIONS ===")
        for exc in exceptions:
            print(json.dumps(exc, indent=2))

    proc.kill()

if __name__ == '__main__':
    asyncio.run(test_error())
