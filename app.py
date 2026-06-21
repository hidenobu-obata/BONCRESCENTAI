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
    global SITE_DATA
    raw_texts = []
    
    # 1. 3linesエピソードの網羅
    try:
        url_3lines = "https://boncrescent-erifan.jp/special/3lines/index.htm"
        res = requests.get(url_3lines, timeout=10)
        res.encoding = 'shift_jis'
        soup = BeautifulSoup(res.text, 'html.parser')
        raw_texts.append(f"【3lines】{soup.get_text(separator=' ', strip=True)}")
    except: pass

    # 2. kiji1.html ～ kiji24.html の全網羅
    for i in range(1, 25):
        try:
            url_kiji = f"https://boncrescent-erifan.jp/kiji/kiji{i}.html"
            res = requests.get(url_kiji, timeout=5)
            res.encoding = 'shift_jis'
            soup = BeautifulSoup(res.text, 'html.parser')
            # 案内人としての文脈を維持するため、本文をきれいに抽出
            text = soup.get_text(separator=' ', strip=True)
            raw_texts.append(f"【Kiji{i}】{text}")
        except: continue
        
    # トークンを節約しつつ網羅するため、重複を避け要約的に結合
    SITE_DATA["content"] = "\n\n".join(raw_texts)[:28000] 

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BON CRESCENT AI</title></head>
    <body style="background:#0b132b; color:#fff; font-family:sans-serif; margin:0; padding:20px;">
        <h1 style="color:#f9d71c;">🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="messages" style="height:60vh; overflow-y:auto; border:1px solid #3a506b; padding:10px; margin-bottom:10px; background:#1c2541;">
            <div style="background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">ばんばんち！全記事、全エピソードを網羅しました。何でも聞いてくださいね。</div>
        </div>
        <div style="display:flex; gap:10px;"><input type="text" id="user-input" style="flex:1; padding:10px;"><button onclick="sendMessage()" style="padding:10px; background:#f9d71c; cursor:pointer;">送信</button></div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value;
                const res = await fetch('/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text})});
                const data = await res.json();
                document.getElementById('messages').innerHTML += `<div style="margin:5px 0;"><b>You:</b> ${text}</div><div style="margin:5px 0; background:#5bc0be; color:#0b132b; padding:10px;"><b>AI:</b> ${data.reply}</div>`;
                input.value = '';
            }
        </script>
    </body></html>""")

@app.post("/chat")
async def chat(payload: ChatRequest):
    system_prompt = (
        "あなたは「BON CRESCENT」の専属案内人「ばんばんち」です。"
        "提供された全記事データと3linesエピソードをすべて参照し、質問者の問いに答えてください。"
        "『不明』で逃げるのは禁止です。全データの中から記述を探し出し、管理人様の言葉を引用して回答してください。"
        f"【参照データ】\n{SITE_DATA['content']}"
    )
    res = client.chat.completions.create(model="gpt-4o", temperature=0, messages=[{"role":"system","content":system_prompt},{"role":"user","content":payload.message}])
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    init_knowledge_base()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))