import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# サイトの全内容を記憶する変数
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
            # コンテンツをより広く抽出する
            text = soup.get_text(separator=' ', strip=True)
            raw_data.append(f"URL: {url}\nTEXT: {text}")
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
        <title>平松愛理ファンサイトBON CRESCENT AI</title>
        <style>
            body { background: #0b132b; color: #f4f4f9; font-family: sans-serif; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; }
            #container { width: 100%; max-width: 600px; }
            h1 { color: #f9d71c; text-align: center; }
            #messages { height: 60vh; overflow-y: auto; border: 1px solid #3a506b; padding: 10px; margin-bottom: 10px; background: #1c2541; border-radius: 5px; }
            #input-area { display: flex; gap: 5px; }
            input { flex: 1; padding: 10px; border-radius: 5px; border: none; font-size: 16px; }
            button { padding: 10px 15px; border-radius: 5px; border: none; background: #f9d71c; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
            <div id="messages">
                <div style="background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">ばんばんち。「BON CRESCENT」の案内人です。サイト内のすべての知識を総動員して回答します。何でもお聞きください！</div>
            </div>
            <div id="input-area">
                <input type="text" id="user-input" placeholder="メッセージを入力...">
                <button onclick="sendMessage()">送信</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value;
                if(!text) return;
                document.getElementById('messages').innerHTML += `<div style="margin:5px 0; text-align:right;">${text}</div>`;
                const res = await fetch('/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text})});
                const data = await res.json();
                document.getElementById('messages').innerHTML += `<div style="margin:5px 0; background:#5bc0be; color:#0b132b; padding:5px;">${data.reply}</div>`;
                input.value = '';
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            }
        </script>
    </body>
    </html>
    """)

@app.post("/chat")
async def chat(payload: ChatRequest):
    # 【絶対重要】管理人様のサイトにある言葉を直接探させる指示
    system_prompt = (
        "あなたは平松愛理ファンサイト「BON CRESCENT」の専属AI案内人です。"
        "質問に対し、提供された【参照データ】を必ず全文スキャンして回答してください。"
        "兄、家族、娘(初一音さん)、楽曲数(MIDI:243, 楽譜:185, ボカロ:237, 音ゲー:216)などの情報は、必ずデータに含まれています。"
        "もし直接的な記述が弱くても、関連する文脈を読み取って管理人様の意図に沿った回答をすること。"
        "『分かりません』ではなく、サイト内の情報を徹底的に探して案内してください。"
        f"【参照データ】\n{SITE_DATA['content']}"
    )
    res = client.chat.completions.create(model="gpt-4o", temperature=0, messages=[{"role":"system","content":system_prompt},{"role":"user","content":payload.message}])
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    init_knowledge_base()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))