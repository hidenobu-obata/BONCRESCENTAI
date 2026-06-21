import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# データをリストで保持
def load_data():
    try:
        with open("data.txt", "r", encoding="shift_jis", errors="ignore") as f:
            return f.readlines()
    except:
        return []

DATA_LINES = load_data()

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
            body { background: #0b132b; color: #f4f4f9; font-family: sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
            h1 { color: #f9d71c; text-align: center; font-size: 1.5rem; }
            #chat-container { width: 95%; max-width: 600px; background: #1c2541; border-radius: 10px; padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
            #messages { height: 60vh; overflow-y: auto; border-bottom: 1px solid #3a506b; padding: 10px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .user { background: #3a506b; text-align: right; }
            .bot { background: #5bc0be; color: #0b132b; }
            input { width: 100%; padding: 10px; border-radius: 5px; border: none; box-sizing: border-box; }
            button { background: #f9d71c; width: 100%; padding: 10px; border-radius: 5px; border: none; cursor: pointer; font-weight: bold; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h1>🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="chat-container">
            <div id="messages"><div class="message bot">ばんばんち。検索を最適化しました。何でも聞いてください。</div></div>
            <input type="text" id="user-input" placeholder="質問を入力...">
            <button onclick="sendMessage()">送信</button>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value.trim();
                if (!text) return;
                const msgDiv = document.getElementById('messages');
                msgDiv.innerHTML += `<div class="message user">${text}</div>`;
                const query = text; input.value = '';
                const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: query })});
                const data = await res.json();
                msgDiv.innerHTML += `<div class="message bot">${data.reply}</div>`;
                msgDiv.scrollTop = msgDiv.scrollHeight;
            }
        </script>
    </body>
    </html>
    """)

@app.post("/chat")
async def chat(payload: dict):
    query = payload.get("message", "")
    # キーワードマッチする行だけを抜き出す（高速化の肝）
    relevant = [line for line in DATA_LINES if any(k in line for k in query.split())]
    context = "".join(relevant[:10]) # 関連する10行のみをAIに送る
    
    # 関連情報がなければ最初の方のデータを送る
    if not context:
        context = "".join(DATA_LINES[:10])

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"あなたは「ばんばんち」。以下の【抜粋データ】を元に回答せよ。【抜粋データ】\n{context}"},
                {"role": "user", "content": query}
            ]
        )
        return {"reply": res.choices[0].message.content}
    except Exception:
        return {"reply": "サーバーが混雑しています。再度入力してください。"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))