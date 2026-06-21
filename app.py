import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# メモリ保持用
KNOWLEDGE_BASE = {}

# 起動時に全コンテンツを網羅・保持
@app.on_event("startup")
def init_knowledge_base():
    global KNOWLEDGE_BASE
    urls = {
        "index": "https://boncrescent-erifan.jp/index.html",
        "3lines": "https://boncrescent-erifan.jp/special/3lines/index.htm",
        "bonroom": "https://boncrescent-erifan.jp/salon/bonroom.htm"
    }
    for i in range(1, 25):
        urls[f"kiji{i}"] = f"https://boncrescent-erifan.jp/kiji/kiji{i}.html"
    
    for key, url in urls.items():
        try:
            res = requests.get(url, timeout=10)
            res.encoding = 'shift_jis'
            soup = BeautifulSoup(res.text, 'html.parser')
            for s in soup(["script", "style", "nav", "footer"]): s.decompose()
            KNOWLEDGE_BASE[key] = soup.get_text(separator=' ', strip=True)
        except: continue

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
            body { background-color: #0b132b; color: #f4f4f9; font-family: sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
            h1 { color: #f9d71c; text-align: center; font-size: 1.5rem; }
            #chat-container { width: 95%; max-width: 600px; background: #1c2541; border-radius: 10px; padding: 15px; box-sizing: border-box; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
            #messages { height: 60vh; overflow-y: auto; border-bottom: 1px solid #3a506b; padding-bottom: 15px; margin-bottom: 15px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; line-height: 1.4; }
            .user { background: #3a506b; margin-left: auto; text-align: right; width: fit-content; max-width: 80%; }
            .bot { background: #5bc0be; color: #0b132b; width: fit-content; max-width: 80%; }
            #input-area { display: flex; gap: 10px; }
            input { flex: 1; padding: 10px; border-radius: 5px; border: none; font-size: 16px; }
            button { background: #f9d71c; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }
            @media (max-width: 480px) { h1 { font-size: 1.2rem; } }
        </style>
    </head>
    <body>
        <h1>🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="chat-container">
            <div id="messages">
                <div class="message bot">ばんばんち。「BON CRESCENT」の案内人です。全データを読み込みました。何でもお聞きください。</div>
            </div>
            <div id="input-area">
                <input type="text" id="user-input" placeholder="メッセージを入力...">
                <button onclick="sendMessage()">送信</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value.trim();
                if (!text) return;
                const msgDiv = document.getElementById('messages');
                msgDiv.innerHTML += `<div class="message user">${text}</div>`;
                input.value = '';
                const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: text })});
                const data = await res.json();
                msgDiv.innerHTML += `<div class="message bot">${data.reply}</div>`;
                msgDiv.scrollTop = msgDiv.scrollHeight;
            }
        </script>
    </body>
    </html>
    """)

@app.post("/chat")
async def chat(payload: ChatRequest):
    # 全データを統合して参照
    all_knowledge = "\n\n".join(KNOWLEDGE_BASE.values())
    
    system_prompt = (
        "あなたは平松愛理ファンサイト「BON CRESCENT」の専属案内人「ばんばんち」です。"
        "質問に対し、提供された全データ（記事24本、3lines、bonroom、index）を根拠として回答してください。"
        "外部知識は一切含めず、データにある事実のみを管理人様の言葉を尊重して伝えてください。"
        "回答は迅速に行い、データに見当たらない場合は正直にその旨を伝えてください。"
        f"【参照データ】\n{all_knowledge}"
    )
    
    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": payload.message}]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))