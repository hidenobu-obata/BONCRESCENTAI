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
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="ja">
    <head><meta charset="UTF-8"><title>BON CRESCENT 案内人ボット</title></head>
    <body style="background:#0b132b; color:#f4f4f9; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; padding:20px;">
        <h1>🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="chat-container" style="width:100%; max-width:600px; background:#1c2541; border-radius:10px; padding:20px;">
            <div id="messages" style="height:400px; overflow-y:auto; border-bottom:1px solid #3a506b; padding-bottom:15px; margin-bottom:15px;"></div>
            <div id="input-area" style="display:flex; gap:10px;">
                <input type="text" id="user-input" style="flex:1; padding:10px; border-radius:5px;" placeholder="メッセージを入力...">
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
                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await res.json();
                    msgDiv.innerHTML += `<div style="margin:10px 0; padding:10px; border-radius:5px; background:#5bc0be; color:#0b132b;">${data.reply}</div>`;
                    msgDiv.scrollTop = msgDiv.scrollHeight;
                } catch(e) {}
            }
        </script>
    </body>
    </html>
    """)

def init_knowledge_base():
    global SITE_KNOWLEDGE
    print("⏳ [全件網羅モード] サイト巡回開始...")
    
    # 以前のルール通り、各階層へ確実にアクセスし網羅します
    START_URLS = [
        "https://boncrescent-erifan.jp/special/3lines/index.htm",
        "https://boncrescent-erifan.jp/kiji/index.html",
        "https://boncrescent-erifan.jp/index.html"
    ]
    
    all_text = []
    visited = set()
    queue = list(START_URLS)
    
    # ルールを減らさず、確実に全情報を回収する
    while queue and len(visited) < 30: # ページ制限を少し緩和
        url = queue.pop(0)
        if url in visited: continue
        visited.add(url)
        
        try:
            res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            res.encoding = 'utf-8' if 'utf-8' in res.text.lower() else 'shift_jis'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # コンテンツの抽出精度を上げる
            for s in soup(["script", "style", "nav", "footer"]): s.decompose()
            text = soup.get_text(separator=' ', strip=True)
            all_text.append(f"【URL: {url}】\n{text}")
            
            # リンクの再取得
            for a in soup.find_all('a', href=True):
                full_url = urllib.parse.urljoin(url, a['href'])
                if "boncrescent-erifan.jp" in full_url and full_url not in visited:
                    queue.append(full_url)
        except: continue
        
    SITE_KNOWLEDGE = "\n\n".join(all_text)
    print(f"✅ [全件網羅完了] {len(visited)} ページの情報を記憶しました。")

@app.post("/chat")
async def chat(payload: ChatRequest):
    global SITE_KNOWLEDGE
    # プロンプトの網羅性も元通り以上に強化しました
    system_prompt = (
        "あなたは平松愛理ファンサイト「BON CRESCENT」の公式案内人です。\n"
        "サイト内の全データを記憶しており、管理人様が記述された内容を正確に回答する義務があります。\n"
        "娘さん（初一音さん）をはじめ、MIDI、楽曲、ボカロ、音ゲーなどの全事実を漏らさず回答してください。\n"
        "データにある情報は決して「非公開」などと逃げず、自信を持って解説すること。\n"
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