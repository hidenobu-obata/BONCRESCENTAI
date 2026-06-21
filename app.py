import os
import uvicorn
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI
import threading

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# サイト内の情報を格納するグローバル変数
SITE_DATA = {"content": "情報を収集しています..."}

def fetch_data():
    urls = [
        "https://boncrescent-erifan.jp/",
        "https://boncrescent-erifan.jp/salon/bonroom.htm",
        "https://boncrescent-erifan.jp/special/3lines/index.htm"
    ] + [f"https://boncrescent-erifan.jp/kiji/kiji{i}.html" for i in range(1, 25)]
    
    text = ""
    for url in urls:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                text += BeautifulSoup(res.content, "html.parser").get_text() + "\n"
        except: continue
    SITE_DATA["content"] = text

# 起動と同時に読み込み開始
threading.Thread(target=fetch_data, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>平松愛理ファンサイト BON CRESCENT AI</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
        <style>
            /* 動く青い海の背景設定 */
            body { 
                margin: 0;
                padding: 0;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(270deg, #001f3f, #003366, #00509d, #003366);
                background-size: 800% 800%;
                animation: movingSea 15s ease infinite;
                color: #e0e6ed;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                overflow: hidden;
            }

            @keyframes movingSea {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            #container { 
                width: 90%;
                max-width: 800px; 
                background: rgba(28, 37, 65, 0.85);
                backdrop-filter: blur(10px);
                padding: 30px; 
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            h1 { 
                text-align: center; 
                font-size: 1.8rem;
                margin-bottom: 20px;
                color: #f9d71c; /* 三日月カラー */
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 10px;
            }

            /* 三日月マーク */
            .moon-icon {
                color: #f9d71c;
                filter: drop-shadow(0 0 5px rgba(249, 215, 28, 0.8));
            }

            #chat-box { 
                height: 55vh; 
                overflow-y: auto; 
                padding: 15px; 
                background: rgba(10, 14, 23, 0.6);
                border-radius: 8px;
                margin-bottom: 15px;
                border: 1px solid #3a506b;
                scroll-behavior: smooth;
            }

            .msg { margin-bottom: 15px; line-height: 1.6; }
            .user-msg { color: #fff; font-weight: bold; border-left: 3px solid #f9d71c; padding-left: 10px; }
            .ai-msg { color: #5bc0be; background: rgba(91, 192, 190, 0.1); padding: 10px; border-radius: 5px; }

            .input-group { display: flex; gap: 10px; }
            input { 
                flex-grow: 1; 
                padding: 15px; 
                border-radius: 5px; 
                border: 1px solid #3a506b; 
                background: #0a0e17; 
                color: #fff;
                font-size: 16px;
            }
            button { 
                padding: 0 25px; 
                background: #f9d71c; 
                border: none; 
                border-radius: 5px; 
                font-weight: bold; 
                cursor: pointer; 
                transition: transform 0.2s;
            }
            button:hover { transform: scale(1.05); background: #e6c519; }

            /* スクロールバーのカスタマイズ */
            #chat-box::-webkit-scrollbar { width: 6px; }
            #chat-box::-webkit-scrollbar-thumb { background: #3a506b; border-radius: 10px; }
        </style>
    </head>
    <body>
        <div id="container">
            <h1><i class="fa-solid fa-moon moon-icon"></i> 平松愛理ファンサイト BON CRESCENT AI</h1>
            <div id="chat-box" id="scroll-target"></div>
            <div class="input-group">
                <input type="text" id="q" placeholder="質問を入力してください..." onkeypress="if(event.key==='Enter')send()">
                <button onclick="send()">送信</button>
            </div>
        </div>

        <script>
            async function send(){
                const input = document.getElementById('q');
                const q = input.value;
                if(!q) return;

                const box = document.getElementById('chat-box');
                
                // 自分の質問を表示
                box.innerHTML += `<div class="msg user-msg">自分: ${q}</div>`;
                
                // 【修正】入力欄を即座にクリア
                input.value = '';
                
                // スクロールアップ（最新のメッセージへ）
                box.scrollTop = box.scrollHeight;

                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({msg: q})
                    });
                    const data = await res.json();
                    
                    // ばんばんちの回答を表示
                    box.innerHTML += `<div class="msg ai-msg"><b>ばんばんち:</b> ${data.reply}</div>`;
                    
                    // 【修正】回答後もスクロールアップ
                    box.scrollTop = box.scrollHeight;
                } catch(e) {
                    box.innerHTML += `<div class="msg" style="color:red">通信エラーが発生しました。</div>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(payload: dict):
    msg = payload.get("msg", "")
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":f"あなたは平松愛理ファンサイトBON CRESCENTの案内人「ばんばんち」です。以下のサイト情報を元に回答してください。お兄様（お兄さん）に関する具体的なエピソードもサイト内に含まれているはずです。:{SITE_DATA['content']}"},
            {"role":"user","content":msg}
        ]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))