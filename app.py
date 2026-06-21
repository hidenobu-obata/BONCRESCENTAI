import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# データをリストで保持（起動時に一度だけ）
try:
    with open("data.txt", "r", encoding="shift_jis", errors="ignore") as f:
        DATA_LINES = f.readlines()
except:
    DATA_LINES = ["データが見つかりません。"]

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
        h1 { color: #f9d71c; text-align: center; font-size: 1.5rem; margin-bottom: 20px; }
        #chat-container { width: 100%; max-width: 600px; background: #1c2541; border-radius: 10px; padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        #messages { height: 50vh; overflow-y: auto; border-bottom: 1px solid #3a506b; padding-bottom: 10px; margin-bottom: 10px; }
        .message { margin: 10px 0; padding: 8px; border-radius: 5px; }
        .user { background: #3a506b; text-align: right; }
        .bot { background: #5bc0be; color: #0b132b; }
        #input-area { display: flex; gap: 5px; }
        input { flex: 1; padding: 10px; border-radius: 5px; border: none; }
        button { background: #f9d71c; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
    <div id="chat-container">
        <div id="messages"><div class="message bot">ばんばんち。何でも聞いてください。</div></div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="メッセージを入力...">
            <button onclick="sendMessage()">送信</button>
        </div>
    </div>
    <script>
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const msgDiv = document.getElementById('messages');
            if (!input.value.trim()) return;
            msgDiv.innerHTML += `<div class="message user">${input.value}</div>`;
            const query = input.value; input.value = '';
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
async def chat(payload: ChatRequest):
    # 質問に関連する行だけを抽出（プログラム側で検索）
    query = payload.message
    # 関連する行（質問にキーワードが含まれる行）を最大10行だけ抽出
    context = "\n".join([line for line in DATA_LINES if any(word in line for word in query.split())])
    
    # contextが空なら最近のデータを提示
    if not context:
        context = "\n".join(DATA_LINES[-20:])

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"あなたは案内人「ばんばんち」。以下の【関連データ】のみを根拠に回答せよ。【関連データ】{context}"},
                {"role": "user", "content": query}
            ]
        )
        return {"reply": res.choices[0].message.content}
    except Exception:
        return {"reply": "サーバーが混雑しています。もう一度押してください。"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))