# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ===========================================
# 🔧 データベースURL設定
# ===========================================
# PostgreSQL から SQLite に変更しました
# SQLiteではローカルに employee.db ファイルが自動生成されます
SQLALCHEMY_DATABASE_URL = "sqlite:///./employee.db"

# SQLiteでは check_same_thread=False が必須
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# セッション作成設定
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()


# ===========================================
# 🔧 DBセッション取得用の依存関数
# ===========================================
def get_db():
    """
    FastAPI の依存関数。
    APIリクエストごとにDBセッションを生成・クローズします。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
