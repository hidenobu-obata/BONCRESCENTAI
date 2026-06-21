import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ファイル読み込みをリクエスト時のみに行うことで起動エラーを100%防ぐ
def get_data():
    try:
        with open("data.txt", "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except:
        return "データがありません。"

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BON CRESCENT AI - ばんばんち</title>
        <style>
            body { background: #0a0e17; color: #e0e6ed; font-family: 'Helvetica Neue', sans-serif; margin: 0; display: flex; justify-content: center; }
            #container { width: 100%; max-width: 500px; padding: 20px; box-sizing: border-box; }
            h1 { text-align: center; color: #f9d71c; }
            #chat-box { height: 60vh; overflow-y: auto; border: 1px solid #3a506b; padding: 15px; border-radius: 10px; background: #1c2541; margin-bottom: 10px; }
            .msg { margin: 10px 0; padding: 10px; border-radius: 8px; }
            .user { background: #3a506b; text-align: right; }
            .bot { background: #5bc0be; color: #0b132b; font-weight: bold; }
            input { width: 100%; padding: 12px; border-radius: 5px; border: none; margin-top: 10px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; border-radius: 5px; border: none; background: #f9d71c; color: #0b132b; font-weight: bold; margin-top: 10px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>ばんばんち</h1>
            <div id="chat-box"><div class="msg bot">ばんばんち。何でも聞いてね。</div></div>
            <input type="text" id="q" placeholder="質問を入力...">
            <button onclick="send()">送信</button>
        </div>
        <script>
            async function send() {
                const q = document.getElementById('q').value;
                document.getElementById('chat-box').innerHTML += `<div class="msg user">${q}</div>`;
                const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({msg:q})});
                const data = await res.json();
                document.getElementById('chat-box').innerHTML += `<div class="msg bot">${data.reply}</div>`;
                document.getElementById('q').value = '';
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(payload: dict):
    data = get_data()
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"あなたは「ばんばんち」。以下のデータに基づいて回答してください。\n{data}"},
                  {"role": "user", "content": payload.get("msg")}]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))