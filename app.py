import os
import uvicorn
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from openai import OpenAI
import threading

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# サイト内の情報を格納するグローバル変数
SITE_DATA = {"content": "情報を収集しています..."}

def fetch_data():
    urls = [
        "https://boncrescent-erifan.jp/",
        "https://boncrescent-erifan.jp/salon/bonroom.htm",
        "https://boncrescent-erifan.jp/special/3lines/index.htm"
    ] + [f"https://boncrescent-erifan.jp/kiji/kiji{i}.html" for i in range(1, 25)]
    
    text = ""
    for url in urls:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                text += BeautifulSoup(res.content, "html.parser").get_text() + "\n"
        except: continue
    SITE_DATA["content"] = text

# 起動と同時に読み込み開始
threading.Thread(target=fetch_data, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def index():
    # 本来のBON CRESCENTのデザインに合わせたHTML構造
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>平松愛理ファンサイト BON CRESCENT AI</title>
        <style>
            /* ここにBON CRESCENT本来のCSSを記述してください */
            body { background: #0a0e17; color: #e0e6ed; font-family: sans-serif; margin: 0; }
            #container { max-width: 800px; margin: auto; padding: 20px; }
            #chat-box { height: 60vh; background: #1c2541; overflow-y: auto; padding: 15px; border-radius: 8px; }
            input { width: 100%; padding: 12px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #f9d71c; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>平松愛理ファンサイト BON CRESCENT AI</h1>
            <div id="chat-box"></div>
            <input type="text" id="q" placeholder="質問を入力...">
            <button onclick="send()">送信</button>
        </div>
        <script>
            async function send(){
                const q=document.getElementById('q').value;
                const box=document.getElementById('chat-box');
                box.innerHTML+=`<p>自分: ${q}</p>`;
                const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:q})});
                const data=await res.json();
                box.innerHTML+=`<p><b>ばんばんち:</b> ${data.reply}</p>`;
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(payload: dict):
    # 読み込んだデータから回答
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":f"あなたは平松愛理ファンサイトBON CRESCENTの案内人。以下のサイト情報を元に回答せよ。お兄様に関する情報も記載されているはずです。:{SITE_DATA['content']}"},
            {"role":"user","content":payload.get("msg")}
        ]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))