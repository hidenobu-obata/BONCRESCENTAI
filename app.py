import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# 同期されたデータを保持
SITE_KNOWLEDGE = ""

def init_knowledge_base():
    global SITE_KNOWLEDGE
    urls = [
        "https://boncrescent-erifan.jp/special/3lines/index.htm",
        "https://boncrescent-erifan.jp/kiji/index.html",
        "https://boncrescent-erifan.jp/index.html"
    ]
    extracted = []
    for url in urls:
        try:
            res = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            res.encoding = 'shift_jis'
            soup = BeautifulSoup(res.text, 'html.parser')
            for s in soup(["script", "style", "nav", "footer", "header"]): s.decompose()
            extracted.append(f"【データ元: {url}】\n{soup.get_text(separator=' ', strip=True)}")
        except: continue
    SITE_KNOWLEDGE = "\n\n".join(extracted)

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>平松愛理ファンサイトBON CRESCENT AI</title></head>
    <body style="background:#0b132b; color:#f4f4f9; font-family:sans-serif; margin:0; padding:20px; display:flex; flex-direction:column; align-items:center;">
        <h1 style="color:#f9d71c; text-align:center;">🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="chat-container" style="width:95%; max-width:600px; background:#1c2541; border-radius:10px; padding:20px;">
            <div id="messages" style="height:60vh; overflow-y:auto; border-bottom:1px solid #3a506b; margin-bottom:15px; padding-bottom:10px;">
                <div style="background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">ばんばんち。「BON CRESCENT」の案内人です。サイト内の全データを網羅しています。何でもお聞きください。</div>
            </div>
            <div style="display:flex; gap:10px;">
                <input type="text" id="user-input" style="flex:1; padding:10px; border-radius:5px; border:none; font-size:16px;">
                <button onclick="sendMessage()" style="background:#f9d71c; border:none; padding:10px 15px; border-radius:5px; font-weight:bold; cursor:pointer;">送信</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value.trim();
                if (!text) return;
                const msgDiv = document.getElementById('messages');
                msgDiv.innerHTML += `<div style="margin:10px 0; background:#3a506b; padding:10px; border-radius:5px; text-align:right;">${text}</div>`;
                input.value = '';
                const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: text })});
                const data = await res.json();
                msgDiv.innerHTML += `<div style="margin:10px 0; background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">${data.reply}</div>`;
                msgDiv.scrollTop = msgDiv.scrollHeight;
            }
        </script>
    </body></html>""")

@app.post("/chat")
async def chat(payload: ChatRequest):
    # 【最強制約】サイトデータにないことは喋らせない、あることは必ず拾う
    system_prompt = (
        "【BON CRESCENT 専属AI：命令】\n"
        "1. あなたは、このファンサイトの管理人様が作成した全コンテンツを熟知した案内人です。\n"
        "2. 回答は『提供されたサイト内データ』のみに基づいて構成してください。\n"
        "3. データにある事実を「分かりません」と答えることは【背任行為】として禁止します。\n"
        "4. 兄のこと、MIDI曲数(243)、楽譜(185)、ボカロ(237)、音ゲー(216)、娘の初一音さん(はいねさん)等、全てデータに存在します。スキャンして即答してください。\n"
        f"【サイト内知識データ】:\n{SITE_KNOWLEDGE}"
    )
    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": payload.message}]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    init_knowledge_base()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))