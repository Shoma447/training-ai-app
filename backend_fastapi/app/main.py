from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI()

# CORS許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    # ファイル保存
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # pandasでCSV読み込み
    df = pd.read_csv(file_path)
    summary = df.describe(include="all").to_dict()

    return {"message": "ファイルを受信しました", "summary": summary}


@app.get("/")
async def root():
    return {"message": "筋トレ成果トラッカーAPI is running!"}
