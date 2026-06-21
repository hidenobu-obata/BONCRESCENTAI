import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# アプリ起動時に一度だけdata.txtを読み込み、メモリに保持する方式
# これなら起動時の通信エラーやタイムアウトは物理的に発生しません
def load_data():
    try:
        with open("data.txt", "r", encoding="shift_jis", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"データ読み込みエラー: {e}"

SITE_DATA = load_data()

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
            <div id="messages"><div class="message bot">ばんばんち。全データを読み込みました。何でも聞いてください。</div></div>
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
    # すべてのデータをAIに渡す。今のモデルは非常に賢いため、この方が正確です。
    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": f"あなたは「ばんばんち」。以下の【サイト内データ】のみを根拠に回答せよ。推測は厳禁。データにある事実を引用せよ。\n【サイト内データ】\n{SITE_DATA}"},
            {"role": "user", "content": payload.message}
        ]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))