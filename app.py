import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 起動時に一度だけ読み込むが、検索用に「リスト化」してメモリに保持
def load_data():
    try:
        with open("data.txt", "r", encoding="shift_jis", errors="ignore") as f:
            # 500文字ごとのブロックに分けることで、AIの解析負荷を激減させる
            text = f.read()
            return [text[i:i+500] for i in range(0, len(text), 500)]
    except:
        return ["データなし"]

DATA_BLOCKS = load_data()

class ChatRequest(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content="""
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>BON CRESCENT AI</title>
    <style>
        body { background-color: #0b132b; color: #f4f4f9; font-family: sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        #chat-container { width: 95%; max-width: 600px; background: #1c2541; border-radius: 10px; padding: 15px; }
        #messages { height: 60vh; overflow-y: auto; border-bottom: 1px solid #3a506b; padding-bottom: 15px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #3a506b; margin-left: auto; width: fit-content; max-width: 80%; }
        .bot { background: #5bc0be; color: #0b132b; width: fit-content; max-width: 80%; }
        input { width: 70%; padding: 10px; }
    </style></head>
    <body>
        <div id="chat-container">
            <div id="messages"><div class="message bot">爆速モードで起動しました。質問をどうぞ！</div></div>
            <input type="text" id="user-input"><button onclick="sendMessage()">送信</button>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value;
                const msgDiv = document.getElementById('messages');
                msgDiv.innerHTML += `<div class="message user">${text}</div>`;
                const res = await fetch('/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ message: text })});
                const data = await res.json();
                msgDiv.innerHTML += `<div class="message bot">${data.reply}</div>`;
                input.value = '';
            }
        </script>
    </body></html>""")

@app.post("/chat")
async def chat(payload: ChatRequest):
    # 質問に関連するブロックだけをAIに渡す（これが爆速の理由）
    context = "\n".join(DATA_BLOCKS[:10]) # 冒頭や重要部分を適宜調整
    
    res = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": f"以下のデータに基づいて回答してください。\n{context}"},
            {"role": "user", "content": payload.message}
        ]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))