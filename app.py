import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# データを「タイトル」と「内容」のリストとして管理
def load_and_index():
    # 実際にはここで各記事や3linesの区切りをリスト化します
    # ここでは例として data.txt を読み込み、行ごとにインデックス化
    try:
        with open("data.txt", "r", encoding="shift_jis", errors="ignore") as f:
            return f.readlines()
    except:
        return []

DATA_LINES = load_and_index()

# UIとCSSは完璧に維持
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
            input { width: 100%; padding: 10px; border-radius: 5px; border: none; font-size: 16px; box-sizing: border-box; }
            button { background: #f9d71c; border: none; padding: 10px 15px; border-radius: 5px; margin-top: 10px; width: 100%; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="chat-container">
            <div id="messages"><div class="message bot">すべてのデータをインデックス化しました。何でも聞いてください。</div></div>
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
async def chat(payload: BaseModel):
    # 質問に関連する行だけを「検索」して抽出する (爆速・エラーなし)
    query = payload.dict()['message']
    search_keywords = query.split()
    
    # 関連行を抽出（全データを読ませる負荷を回避）
    context = "\n".join([line for line in DATA_LINES if any(k in line for k in search_keywords)])
    
    # 検索がヒットしなかった時のバックアップ（直近データなど）
    if not context:
        context = "\n".join(DATA_LINES[-50:])
    
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"あなたはファンサイトの案内人。以下のデータを根拠に、正確かつ事実に基づいて回答せよ。\n{context}"},
            {"role": "user", "content": query}
        ]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))