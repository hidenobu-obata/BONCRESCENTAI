import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 全サイトデータを格納する変数
SITE_DATA = {"content": ""}

def init_knowledge_base():
    global SITE_DATA
    raw_texts = []
    # 網羅すべき全URL
    urls = [
        "https://boncrescent-erifan.jp/index.html",
        "https://boncrescent-erifan.jp/special/3lines/index.htm",
        "https://boncrescent-erifan.jp/salon/bonroom.htm"
    ]
    for i in range(1, 25):
        urls.append(f"https://boncrescent-erifan.jp/kiji/kiji{i}.html")
    
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            res.encoding = 'shift_jis' # 文字化け防止
            soup = BeautifulSoup(res.text, 'html.parser')
            for s in soup(["script", "style", "nav", "footer"]): s.decompose()
            raw_texts.append(f"【Source: {url}】 {soup.get_text(separator=' ', strip=True)}")
        except: continue
    
    SITE_DATA["content"] = "\n\n".join(raw_texts)

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
            body { background: #0b132b; color: #fff; font-family: sans-serif; margin: 0; padding: 15px; display: flex; flex-direction: column; align-items: center; }
            #container { width: 100%; max-width: 600px; }
            #messages { height: 50vh; overflow-y: auto; border: 1px solid #3a506b; padding: 10px; background: #1c2541; border-radius: 5px; margin-bottom: 10px; }
            .input-wrap { display: flex; gap: 5px; }
            input { flex: 1; padding: 15px; border-radius: 5px; border: 1px solid #3a506b; font-size: 16px; }
            button { padding: 10px 20px; background: #f9d71c; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>🌙 BON CRESCENT AI</h1>
            <div id="messages"><div style="background:#5bc0be; color:#0b132b; padding:10px; border-radius:5px;">ばんばんち！全記事・全エピソード・全コンテンツを網羅しました。何でも聞いてくださいね。</div></div>
            <div class="input-wrap">
                <input type="text" id="user-input" placeholder="メッセージを入力...">
                <button onclick="sendMessage()">送信</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value;
                if(!text) return;
                document.getElementById('messages').innerHTML += `<div style="margin:5px 0;"><b>You:</b> ${text}</div>`;
                const res = await fetch('/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:text})});
                const data = await res.json();
                document.getElementById('messages').innerHTML += `<div style="margin:5px 0; background:#5bc0be; color:#0b132b; padding:10px;"><b>AI:</b> ${data.reply}</div>`;
                input.value = '';
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            }
        </script>
    </body></html>""")

@app.post("/chat")
async def chat(payload: ChatRequest):
    system_prompt = (
        "あなたは平松愛理ファンサイト「BON CRESCENT」の専属案内人「ばんばんち」です。"
        "提供された全データ（記事24本、3lines、紹介ページ等）に基づき回答してください。"
        "管理人様が書かれた事実のみを根拠とし、推測や外部知識（KANさんなど）は厳禁です。"
        "データに記述がある情報は、その文脈を引用して正確に伝えてください。"
        "データ内に答えがない場合は、正直に「該当する記述は見当たりません」と答えてください。"
        f"【参照データ】\n{SITE_DATA['content']}"
    )
    res = client.chat.completions.create(model="gpt-4o", temperature=0, messages=[{"role":"system","content":system_prompt},{"role":"user","content":payload.message}])
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    init_knowledge_base()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))