import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SITE_DATA = {"content": ""}

def init_knowledge_base():
    urls = [
        "https://boncrescent-erifan.jp/special/3lines/index.htm",
        "https://boncrescent-erifan.jp/kiji/index.html",
        "https://boncrescent-erifan.jp/index.html"
    ]
    raw_data = []
    for url in urls:
        try:
            res = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            res.encoding = 'shift_jis'
            soup = BeautifulSoup(res.text, 'html.parser')
            for s in soup(["script", "style", "nav", "footer", "header"]): s.decompose()
            raw_data.append(f"PAGE: {url}\nCONTENT: {soup.get_text(separator=' ', strip=True)}")
        except: continue
    SITE_DATA["content"] = "\n\n".join(raw_data)

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BON CRESCENT AI</title>
        <style>
            body { background: #0b132b; color: #fff; font-family: sans-serif; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; }
            #container { width: 100%; max-width: 600px; }
            #messages { height: 60vh; overflow-y: auto; border: 1px solid #3a506b; padding: 10px; margin-bottom: 10px; background: #1c2541; border-radius: 5px; }
            #input-area { display: flex; gap: 5px; }
            input { flex: 1; padding: 10px; border-radius: 5px; border: none; font-size: 16px; }
            button { padding: 10px 15px; border-radius: 5px; border: none; background: #f9d71c; font-weight: bold; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>🌙 BON CRESCENT AI</h1>
            <div id="messages">
                <div style="background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">サイトデータを全網羅しました。ご質問ください。</div>
            </div>
            <div id="input-area">
                <input type="text" id="user-input">
                <button onclick="sendMessage()">送信</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value;
                if(!text) return;
                const res = await fetch('/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text})});
                const data = await res.json();
                document.getElementById('messages').innerHTML += `<div style="margin:5px 0;"><b>You:</b> ${text}</div><div style="margin:5px 0; background:#5bc0be; color:#0b132b; padding:5px;"><b>AI:</b> ${data.reply}</div>`;
                input.value = '';
            }
        </script>
    </body>
    </html>
    """)

@app.post("/chat")
async def chat(payload: ChatRequest):
    system_prompt = (
        "あなたはBON CRESCENTの案内人です。提供された全サイトデータに基づき、兄のこと、MIDI曲数、初一音さんのこと等、全ての事実に正確に答えてください。"
        "データ内に答えがない場合は「該当データは見当たりませんでした」と正直に答え、決して「不明」の一言で片付けないでください。"
        f"【参照データ】\n{SITE_DATA['content']}"
    )
    res = client.chat.completions.create(model="gpt-4o", temperature=0, messages=[{"role":"system","content":system_prompt},{"role":"user","content":payload.message}])
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    init_knowledge_base()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))