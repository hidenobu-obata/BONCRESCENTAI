import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_data_lines():
    try:
        with open("data.txt", "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except:
        return []

DATA_LINES = get_data_lines()

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>平松愛理ファンサイト BON CRESCENT AI</title>
        <style>
            body { background: #0a0e17; color: #e0e6ed; font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; display: flex; justify-content: center; }
            #container { width: 100%; max-width: 500px; padding: 20px; box-sizing: border-box; }
            h1 { text-align: center; color: #f9d71c; font-size: 1.5rem; margin-bottom: 5px; }
            .subtitle { text-align: center; font-size: 1rem; color: #5bc0be; margin-bottom: 20px; font-weight: bold; }
            #chat-box { height: 50vh; overflow-y: auto; border: 1px solid #3a506b; padding: 15px; border-radius: 10px; background: #1c2541; margin-bottom: 10px; }
            .msg { margin: 10px 0; padding: 10px; border-radius: 8px; line-height: 1.4; }
            .user { background: #3a506b; text-align: right; color: white; }
            .bot { background: #5bc0be; color: #0b132b; font-weight: bold; }
            input { width: 100%; padding: 12px; border-radius: 5px; border: none; box-sizing: border-box; background: #fff; }
            button { width: 100%; padding: 12px; border-radius: 5px; border: none; background: #f9d71c; color: #0b132b; font-weight: bold; margin-top: 10px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1>平松愛理ファンサイト</h1>
            <div class="subtitle">BON CRESCENT AI - ばんばんち</div>
            <div id="chat-box"><div class="msg bot">ばんばんち。平松愛理さんのこと、何でも聞いてね。</div></div>
            <input type="text" id="q" placeholder="質問を入力...">
            <button onclick="send()">送信</button>
        </div>
        <script>
            async function send() {
                const q = document.getElementById('q').value;
                if(!q) return;
                document.getElementById('chat-box').innerHTML += `<div class="msg user">${q}</div>`;
                document.getElementById('q').value = '';
                const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({msg:q})});
                const data = await res.json();
                document.getElementById('chat-box').innerHTML += `<div class="msg bot">${data.reply}</div>`;
                document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(payload: dict):
    user_query = payload.get("msg", "")
    # 質問に関連しそうな行を抽出し、トークン制限（128k）を確実に回避する量を送信
    relevant_lines = [line for line in DATA_LINES if any(word in line for word in user_query.split())]
    context = "".join(relevant_lines[:80]) if relevant_lines else "".join(DATA_LINES[:40])
    
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"あなたは「ばんばんち」。平松愛理ファンサイトの案内人です。以下の情報を元に回答してください。\n{context}"},
                {"role": "user", "content": user_query}
            ]
        )
        return {"reply": res.choices[0].message.content}
    except Exception as e:
        return {"reply": "ごめんなさい、うまくお答えできませんでした。"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))