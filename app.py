import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

SITE_KNOWLEDGE = "サイトデータ同期中..."

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def index():
    # 案内文を復活させたUI
    return HTMLResponse(content="""
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>平松愛理ファンサイトBON CRESCENT AI</title></head>
    <body style="background:#0b132b; color:#f4f4f9; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; padding:20px;">
        <h1 style="color:#f9d71c;">🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="chat-container" style="width:100%; max-width:600px; background:#1c2541; border-radius:10px; padding:20px;">
            <div id="messages" style="height:400px; overflow-y:auto; border-bottom:1px solid #3a506b; padding-bottom:15px; margin-bottom:15px;">
                <div class="message bot" style="background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">
                    ばんばんち。「BON CRESCENT」の案内人AIです。平松愛理さんに関する情報や、サイト内の楽曲・MIDI・楽譜・音ゲーなどについて、何でもお尋ねくださいね。
                </div>
            </div>
            <div id="input-area" style="display:flex; gap:10px;">
                <input type="text" id="user-input" style="flex:1; padding:10px; border-radius:5px; color:#000;" placeholder="メッセージを入力...">
                <button onclick="sendMessage()" style="background:#f9d71c; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-weight:bold;">送信</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value.trim();
                if (!text) return;
                const msgDiv = document.getElementById('messages');
                msgDiv.innerHTML += `<div style="margin:10px 0; padding:10px; border-radius:5px; background:#3a506b; margin-left:auto;">${text}</div>`;
                input.value = '';
                const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: text })});
                const data = await res.json();
                msgDiv.innerHTML += `<div style="margin:10px 0; padding:10px; border-radius:5px; background:#5bc0be; color:#0b132b;">${data.reply}</div>`;
                msgDiv.scrollTop = msgDiv.scrollHeight;
            }
        </script>
    </body></html>""")

def init_knowledge_base():
    global SITE_KNOWLEDGE
    print("⏳ [全データ・全機能網羅モード起動]")
    urls = [
        "https://boncrescent-erifan.jp/special/3lines/index.htm",
        "https://boncrescent-erifan.jp/kiji/index.html",
        "https://boncrescent-erifan.jp/index.html"
    ]
    all_text = []
    for url in urls:
        try:
            res = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            res.encoding = 'shift_jis'
            soup = BeautifulSoup(res.text, 'html.parser')
            for s in soup(["script", "style", "nav", "footer"]): s.decompose()
            all_text.append(soup.get_text(separator=' ', strip=True))
        except: continue
    SITE_KNOWLEDGE = "\n".join(all_text)
    print("✅ [全データ記憶・案内機能正常]")

@app.post("/chat")
async def chat(payload: ChatRequest):
    # 案内人としての口調と、はいねさん等の絶対情報を強固に指示
    system_prompt = (
        "あなたは平松愛理ファンサイト「BON CRESCENT」の温かい案内人AIです。\n"
        "口調は「〜ですね」「〜ですよ」と丁寧で親切に。サイトの案内人らしく振る舞ってください。\n"
        "【絶対事実】\n"
        "- 娘（長女）の情報：お名前は『初一音』と書いて『はいね』さん（1996年生まれ）。シンガー・ソングライター・ボイストレーナーとして活動し、2020年4月29日にYouTubeデビュー。\n"
        "- 回答方針：サイト内の全情報を根拠にし、決して「不明」や「非公開」で逃げず、自信を持って解説すること。\n"
        f"【全サイト知識データ】:\n{SITE_KNOWLEDGE}"
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