import os
import sys
import traceback
import uvicorn
from fastapi import FastAPI

# ログを詳細に出力する設定
print("--- 起動を開始しました ---", file=sys.stderr)

try:
    app = FastAPI()
    print("FastAPIアプリの作成に成功", file=sys.stderr)
    
    # data.txtの存在確認
    if not os.path.exists("data.txt"):
        print("致命的エラー: data.txtが見つかりません。", file=sys.stderr)
    else:
        print("data.txtを確認しました。", file=sys.stderr)

    @app.get("/")
    def read_root():
        return {"status": "ok"}

except Exception:
    print("--- 起動中にエラーが発生しました ---", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1) # これが「Application exited early」の正体です

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"ポート {port} で起動を試みます...", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)