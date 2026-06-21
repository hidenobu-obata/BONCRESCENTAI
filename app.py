import os
import uvicorn
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI
import threading

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# URLリスト
TARGET_URLS = [
    "https://boncrescent-erifan.jp/",
    "https://boncrescent-erifan.jp/salon/bonroom.htm",
    "https://boncrescent-erifan.jp/eridata/ivents.htm",
    "https://boncrescent-erifan.jp/special/3lines/index.htm"
]
TARGET_URLS.extend([f"https://boncrescent-erifan.jp/kiji/kiji{i}.html" for i in range(1, 25)])

SITE_DATA = "情報を収集中です。もう少々お待ちください..."

def load_data():
    global SITE_DATA
    scraped_text = ""
    for url in TARGET_URLS:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                scraped_text += BeautifulSoup(res.content, "html.parser").get_text() + "\n"
        except: continue
    SITE_DATA = scraped_text

threading.Thread(target=load_data, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def index():
    # タイトルを「平松愛理ファンサイト BON CRESCENT AI」に修正
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>平松愛理ファンサイト BON CRESCENT AI</title>
    <style>
        body{background:#0a0e17;color:#fff;font-family:sans-serif;padding:20px;display:flex;justify-content:center;}
        #container{width:100%;max-width:600px;}
        #chat-box{height:400px;background:#1c2541;overflow-y:auto;padding:10px;border-radius:8px;}
        input,button{width:100%;padding:15px;margin-top:10px;border-radius:5px;border:none;}
        button{background:#f9d71c;font-weight:bold;cursor:pointer;}
    </style></head>
    <body>
        <div id="container"><h1>平松愛理ファンサイト BON CRESCENT AI</h1><div id="chat-box"></div>
        <input type="text" id="q" placeholder="質問を入力..."><button onclick="send()">送信</button></div>
        <script>
            async function send(){
                const q=document.getElementById('q').value;
                const box=document.getElementById('chat-box');
                box.innerHTML+=`<p>自分: ${q}</p>`;
                const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:q})});
                const data=await res.json();
                box.innerHTML+=`<p style='color:#5bc0be'>ばんばんち: ${data.reply}</p>`;
            }
        </script>
    </body></html>
    """

@app.post("/chat")
async def chat(payload: dict):
    msg = payload.get("msg", "")
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":f"あなたは平松愛理ファンサイトの案内人「ばんばんち」です。以下のサイト情報から回答して:{SITE_DATA}"},{"role":"user","content":msg}]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))