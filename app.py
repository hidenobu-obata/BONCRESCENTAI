import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 全てのデータを格納する辞書
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
            # タイトルと本文の構造を維持して連結する
            page_title = soup.title.string if soup.title else "無題"
            page_body = soup.get_text(separator=' ', strip=True)
            raw_data.append(f"PAGE_TITLE: {page_title}\nCONTENT: {page_body}")
        except: continue
    SITE_DATA["content"] = "\n\n".join(raw_data)

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>BON CRESCENT AI</title></head>
    <body style="background:#0b132b; color:#fff; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; padding:20px;">
        <h1 style="color:#f9d71c;">🌙 BON CRESCENT AI</h1>
        <div id="messages" style="width:100%; max-width:600px; height:400px; overflow-y:auto; border:1px solid #3a506b; padding:10px; margin-bottom:10px;">
            <div style="background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">ご質問ください。サイト内の全てのデータをスキャンして回答します。</div>
        </div>
        <div style="width:100%; max-width:600px; display:flex; gap:10px;">
            <input type="text" id="user-input" style="flex:1; padding:10px;">
            <button onclick="sendMessage()" style="padding:10px;">送信</button>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value;
                const res = await fetch('/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text})});
                const data = await res.json();
                document.getElementById('messages').innerHTML += `<div style="margin:5px;"><b>You:</b> ${text}</div><div style="margin:5px; background:#5bc0be; color:#0b132b;"><b>AI:</b> ${data.reply}</div>`;
            }
        </script>
    </body></html>""")

@app.post("/chat")
async def chat(payload: ChatRequest):
    # 兄を含む全情報を強制参照させる指示
    system_prompt = (
        "【絶対厳守】あなたは「BON CRESCENT」の全データを記憶しています。\n"
        "質問には【以下のデータ】からのみ回答してください。データにないことは喋らないでください。\n"
        "ただし、データ内にある「兄」「家族」「MIDI数」等は必ず正確に引用して答えること。\n"
        "もしデータ内に答えがなければ、管理人に問い合わせるよう促してください（『分かりません』と即座に切り捨てるのは禁止）。\n"
        f"【参照データ】\n{SITE_DATA['content']}"
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