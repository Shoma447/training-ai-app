import uvicorn
import sys
from pathlib import Path

# ======== 重要: appディレクトリを絶対パスで追加 ========
APP_DIR = Path(__file__).resolve().parent / "app"
sys.path.insert(0, str(APP_DIR))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(APP_DIR)]  # この行も重要
    )
