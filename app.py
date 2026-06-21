import os
import uvicorn
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
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

# サイト内の情報を自動収集してメモリに蓄積する関数
def scrape_data():
    full_text = ""
    for url in TARGET_URLS:
        try:
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.content, "html.parser")
            full_text += soup.get_text() + "\n"
        except:
            continue # 読み込めないページは無視
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
        <title>平松愛理ファンサイト BON CRESCENT AI</title>
        <style>
            body { background: #0a0e17; color: #e0e6ed; font-family: sans-serif; margin: 0; display: flex; justify-content: center; }
            #container { width: 100%; max-width: 500px; padding: 20px; box-sizing: border-box; }
            h1 { text-align: center; color: #f9d71c; }
            .subtitle { text-align: center; color: #5bc0be; margin-bottom: 20px; }
            #chat-box { height: 50vh; overflow-y: auto; border: 1px solid #3a506b; padding: 15px; border-radius: 10px; background: #1c2541; }
            input { width: 100%; padding: 12px; margin-top: 10px; border-radius: 5px; }
            button { width: 100%; padding: 12px; background: #f9d71c; border-radius: 5px; margin-top: 10px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>平松愛理ファンサイト</h1>
            <div class="subtitle">BON CRESCENT AI - ばんばんち</div>
            <div id="chat-box"><div class="msg">ばんばんち。何でも聞いてね。</div></div>
            <input type="text" id="q" placeholder="質問を入力...">
            <button onclick="send()">送信</button>
        </div>
        <script>
            async function send() {
                const q = document.getElementById('q').value;
                const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({msg:q})});
                const data = await res.json();
                document.getElementById('chat-box').innerHTML += `<div class="msg"><b>あなた:</b> ${q}<br><b>ばんばんち:</b> ${data.reply}</div>`;
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(payload: dict):
    user_query = payload.get("msg", "")
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"あなたは平松愛理ファンサイトの案内人です。以下のサイト情報から正確に回答してください。\n{SITE_DATA}"},
            {"role": "user", "content": user_query}
        ]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))