import os
import uvicorn
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI
import threading

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# サイト内の情報を格納する箱（最初は空）
SITE_DATA = {"content": "情報を収集しています。しばらくお待ちください..."}

def fetch_data():
    urls = [
        "https://boncrescent-erifan.jp/",
        "https://boncrescent-erifan.jp/salon/bonroom.htm",
        "https://boncrescent-erifan.jp/eridata/ivents.htm",
        "https://boncrescent-erifan.jp/special/3lines/index.htm"
    ] + [f"https://boncrescent-erifan.jp/kiji/kiji{i}.html" for i in range(1, 25)]
    
    text = ""
    for url in urls:
        try:
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                text += BeautifulSoup(res.content, "html.parser").get_text() + "\n"
        except: continue
    SITE_DATA["content"] = text

# 起動とは別スレッドで裏で読み込むので、起動は即完了します
threading.Thread(target=fetch_data, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head><meta charset="UTF-8"><title>平松愛理ファンサイト BON CRESCENT AI</title></head>
    <body style="background:#0a0e17;color:#fff;font-family:sans-serif;padding:20px;">
        <div style="max-width:600px;margin:auto;">
            <h1>平松愛理ファンサイト BON CRESCENT AI</h1>
            <div id="box" style="height:300px;background:#1c2541;overflow-y:auto;padding:10px;"></div>
            <input type="text" id="q" style="width:100%;padding:10px;margin-top:10px;">
            <button onclick="send()" style="width:100%;padding:10px;background:#f9d71c;">送信</button>
        </div>
        <script>
            async function send(){
                const q=document.getElementById('q').value;
                const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:q})});
                const data=await res.json();
                document.getElementById('box').innerHTML+=`<p>ばんばんち: ${data.reply}</p>`;
            }
        </script>
    </body></html>
    """

@app.post("/chat")
async def chat(payload: dict):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":f"あなたは平松愛理ファンサイトの案内人。情報:{SITE_DATA['content']}"},{"role":"user","content":payload.get("msg")}]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))