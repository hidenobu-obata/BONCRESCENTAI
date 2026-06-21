import os
import uvicorn
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

# 質問が来た時だけ、指定URLを見に行く（起動は一切止まらない）
def get_site_content(url):
    try:
        res = requests.get(url, timeout=5)
        return BeautifulSoup(res.content, "html.parser").get_text()
    except:
        return "情報取得失敗"

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head><meta charset="UTF-8"><title>平松愛理ファンサイト BON CRESCENT AI</title></head>
    <body style="background:#0a0e17;color:#fff;font-family:sans-serif;padding:20px;">
        <div style="max-width:600px;margin:auto;">
            <h1>平松愛理ファンサイト BON CRESCENT AI</h1>
            <div id="box" style="height:300px;background:#1c2541;overflow-y:auto;padding:10px;border:1px solid #3a506b;"></div>
            <input type="text" id="q" style="width:100%;padding:10px;margin-top:10px;box-sizing:border-box;">
            <button onclick="send()" style="width:100%;padding:10px;background:#f9d71c;font-weight:bold;cursor:pointer;margin-top:10px;">送信</button>
        </div>
        <script>
            async function send(){
                const q=document.getElementById('q').value;
                const box=document.getElementById('box');
                box.innerHTML+=`<p>自分: ${q}</p>`;
                const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:q})});
                const data=await res.json();
                box.innerHTML+=`<p style='color:#5bc0be'>ばんばんち: ${data.reply}</p>`;
            }
        </script>
    </body></html>
    """

@app.post("/chat")
async def chat(payload: dict):
    # 質問に関連しそうなURLを一つだけ、即座に読み込む
    content = get_site_content("https://boncrescent-erifan.jp/")
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":f"あなたは平松愛理ファンサイトの案内人。情報:{content}"},{"role":"user","content":payload.get("msg")}]
    )
    return {"reply": res.choices[0].message.content}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))