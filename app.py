import os
import uvicorn
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# サイトのURLリスト
BASE_URL = "https://boncrescent-erifan.jp"
TARGET_URLS = [f"{BASE_URL}/kiji/kiji{i}.html" for i in range(1, 25)]
TARGET_URLS.extend([
    f"{BASE_URL}/salon/bonroom.htm",
    f"{BASE_URL}/eridata/ivents.htm",
    f"{BASE_URL}/special/3lines/index.htm"
])

def scrape_data():
    full_text = ""
    for url in TARGET_URLS:
        try:
            res = requests.get(url, timeout=3)
            soup = BeautifulSoup(res.content, "html.parser")
            full_text += soup.get_text() + "\n"
        except: continue
    return full_text

SITE_DATA = scrape_data()

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BON CRESCENT AI</title>
        <style>
            body { font-family: sans-serif; background: #0a0e17; color: #fff; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
            #container { width: 100%; max-width: 600px; }
            #chat-box { width: 100%; height: 400px; background: #1c2541; overflow-y: scroll; padding: 10px; border-radius: 8px; margin-bottom: 10px; }
            input { width: 100%; padding: 15px; border-radius: 5px; border: none; box-sizing: border-box; }
            button { width: 100%; padding: 15px; margin-top: 10px; background: #f9d71c; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>BON CRESCENT AI</h1>
            <div id="chat-box"></div>
            <input type="text" id="q" placeholder="メッセージを入力...">
            <button id="send-btn" onclick="send()">送信する</button>
        </div>
        <script>
            async function send() {
                const input = document.getElementById('q');
                const box = document.getElementById('chat-box');
                const msg = input.value;
                if(!msg) return;
                box.innerHTML += `<p><b>自分:</b> ${msg}</p>`;
                input.value = '';
                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({msg: msg})
                    });
                    const data = await res.json();
                    box.innerHTML += `<p style="color:#5bc0be"><b>ばんばんち:</b> ${data.reply}</p>`;
                } catch(e) { box.innerHTML += `<p style="color:red">エラーが発生しました</p>`; }
                box.scrollTop = box.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(payload: dict):
    msg = payload.get("msg", "")
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"以下のサイトデータに基づき回答せよ\n{SITE_DATA}"}, {"role": "user", "content": msg}]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))