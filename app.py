import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()

# ==================================================================
# 【重要】OpenAI APIキーの設定 (Render環境変数から読み込み)
# ==================================================================
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# 収集したデータを安全なサイズで全件保持する変数
SITE_KNOWLEDGE = "サイトデータがまだ読み込まれていません。"

class ChatRequest(BaseModel):
    message: str

# ==================================================================
# 1. 本番仕様の画面（HTML）を表示するルート
# ==================================================================
@app.get("/", response_class=HTMLResponse)
async def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>平松愛理ファンサイトBON CRESCENT AI</title>
        <style>
            body { background-color: #0b132b; color: #f4f4f9; font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
            h1 { color: #f9d71c; text-shadow: 0 0 10px rgba(249, 215, 28, 0.5); }
            #chat-container { width: 100%; max-width: 600px; background: #1c2541; border-radius: 10px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            #messages { height: 400px; overflow-y: auto; border-bottom: 1px solid #3a506b; padding-bottom: 15px; margin-bottom: 15px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 5px; max-width: 80%; white-space: pre-wrap; }
            .user { background: #3a506b; margin-left: auto; text-align: right; }
            .bot { background: #5bc0be; color: #0b132b; }
            #input-area { display: flex; gap: 10px; }
            input { flex: 1; padding: 10px; border-radius: 5px; border: none; font-size: 16px; color: #000; }
            button { background: #f9d71c; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px; }
        </style>
    </head>
    <body>
        <h1>🌙 平松愛理ファンサイトBON CRESCENT AI</h1>
        <div id="chat-container">
            <div id="messages">
                <div class="message bot">ばんばんち。「BON CRESCENT」のBON：AIです。平松愛理さんに関する情報や、サイトのコンテンツについて何でもお尋ねくださいね。</div>
            </div>
            <div id="input-area">
                <input type="text" id="user-input" placeholder="メッセージを入力..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">送信</button>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const text = input.value.trim();
                if (!text) return;

                appendMessage(text, 'user');
                input.value = '';

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await response.json();
                    appendMessage(data.reply, 'bot');
                } catch (error) {
                    appendMessage("通信エラーが発生しました。", 'bot');
                }
            }

            function appendMessage(text, sender) {
                const msgDiv = document.getElementById('messages');
                const newMsg = document.createElement('div');
                newMsg.className = `message ${sender}`;
                newMsg.innerText = text;
                msgDiv.appendChild(newMsg);
                msgDiv.scrollTop = msgDiv.scrollHeight;
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ==================================================================
# 2. アプリ起動時にバックグラウンドで全自動実行される同期関数
# ==================================================================
def init_knowledge_base():
    global SITE_KNOWLEDGE
    print("⏳ [本番初期化] サイトデータの自動同期を開始します...")
    
    START_URLS = [
        "https://boncrescent-erifan.jp/special/3lines/index.htm",
        "https://boncrescent-erifan.jp/kiji/index.html",
        "https://boncrescent-erifan.jp/index.html"
    ]
    
    visited_urls = set()
    urls_to_visit = list(START_URLS)
    all_text_data = []
    base_domain = urllib.parse.urlparse(START_URLS[2]).netloc

    try:
        while urls_to_visit and len(visited_urls) < 15:
            current_url = urls_to_visit.pop(0)
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                res = requests.get(current_url, headers=headers, timeout=8)
                res.encoding = 'utf-8' if 'utf-8' in res.text.lower() else 'shift_jis'
                if res.status_code != 200:
                    continue
            except:
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urllib.parse.urljoin(current_url, href)
                if urllib.parse.urlparse(full_url).netloc == base_domain:
                    if full_url not in visited_urls:
                        urls_to_visit.append(full_url)

            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            title = soup.title.string if soup.title else "無題"
            text = soup.get_text()
            clean_text = " ".join(text.split())
            
            if "special/3lines" in current_url:
                all_text_data.append(f"【絶対重要ソース: {title} ({current_url})】\n{clean_text}")
            else:
                all_text_data.append(f"【ソース: {title} ({current_url})】\n{clean_text[:400]}")

        SITE_KNOWLEDGE = "\n\n".join(all_text_data)
        print("✅ [初期化完了] データを正常に記憶しました！")
    except Exception as e:
        print(f"❌ [初期化エラー] {str(e)}")

# ==================================================================
# 3. チャットの返答を処理するルート
# ==================================================================
@app.post("/chat")
async def chat(payload: ChatRequest):
    global SITE_KNOWLEDGE
    user_message = payload.message
    
    system_prompt = (
        "あなたは平松愛理さんのファンサイト「BON CRESCENT」の案内人AIです。"
        "同期されたデータをもとに、管理人様が書かれた真実を忠実に回答してください。\n"
        "【システム確定データ】\n"
        "- 娘（長女）の情報：お名前は『初一音』と書いて、読み方は『はいね』さん（1996年生まれ）。\n"
        f"【サイト内テキスト】:\n{SITE_KNOWLEDGE}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        ai_reply = f"申し訳ありません。エラーが発生しました: {str(e)}"

    return {"reply": ai_reply}

if __name__ == "__main__":
    import uvicorn
    init_knowledge_base()
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)