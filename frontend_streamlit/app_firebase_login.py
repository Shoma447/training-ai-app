# app_firebase_login.py
import os
import platform
from datetime import date
import re
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ===== Firebase（公式SDK） =====
import json
import firebase_admin
from firebase_admin import credentials, auth

# =========================
# ✅ Firebase初期化（Cloud or Local 両対応）
# =========================
if "FIREBASE_CREDENTIALS" in st.secrets:
    # ✅ Streamlit Cloud用（SecretsからJSONを直接読み込み）
    firebase_creds = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(firebase_creds)
else:
    # ✅ ローカル開発用（.env + JSONファイル）
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if not creds_path or not os.path.exists(creds_path):
        st.error(f"❌ Firebase 認証ファイルが見つかりません: {creds_path}")
        st.stop()

    cred = credentials.Certificate(creds_path)

# Firebaseアプリ初期化
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# =========================
# 日本語フォント設定
# =========================
def set_japanese_font():
    os_name = platform.system()
    if os_name == "Windows":
        font_name = "Meiryo"
    elif os_name == "Darwin":
        font_name = "Hiragino Maru Gothic Pro"
    else:
        font_name = "IPAexGothic"
    plt.rcParams["font.family"] = font_name
    sns.set(font=font_name, style="whitegrid")

set_japanese_font()

# =========================
# DB接続設定
# =========================
# Secretsまたは.envのどちらかから取得
DATABASE_URL = st.secrets.get("DATABASE_URL") if "DATABASE_URL" in st.secrets else os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("❌ DATABASE_URL が設定されていません。")
    st.stop()

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class TrainingRecord(Base):
    __tablename__ = "training_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    date = Column(Date, index=True)
    body_part = Column(String, index=True)
    exercise = Column(String, index=True)
    weight = Column(Float)
    reps = Column(Integer)
    volume = Column(Float)

Base.metadata.create_all(bind=engine)

# =========================
# Streamlit設定
# =========================
st.set_page_config(page_title="AI Kintore v2.5 + Firebase Admin Login", layout="wide")
session = SessionLocal()

# =========================
# ログインUI（firebase_admin認証）
# =========================
def login_view():
    st.title("🔐 Firebase ログイン / 新規登録")

    mode = st.radio("モードを選択", ["ログイン", "新規登録"], horizontal=True)
    email = st.text_input("📧 メールアドレス")
    password = st.text_input("🔑 パスワード", type="password")

    if mode == "新規登録":
        if st.button("新規登録"):
            try:
                user = auth.create_user(email=email, password=password)
                st.success(f"✅ 登録完了: {user.email}")
            except Exception as e:
                st.error(f"登録に失敗しました: {e}")
    else:
        if st.button("ログイン"):
            try:
                user = auth.get_user_by_email(email)
                st.session_state["user_uid"] = user.uid
                st.session_state["user_email"] = user.email
                st.success(f"ようこそ {user.email} さん！")
                st.rerun()
            except Exception as e:
                st.error(f"ログインエラー: {e}")

# =========================
# 共通関数（ユーザー別）
# =========================
def load_df():
    uid = st.session_state.get("user_uid")
    if not uid:
        return pd.DataFrame(columns=["ID", "日付", "部位", "種目", "重量(kg)", "回数", "ボリューム"])
    recs = session.query(TrainingRecord).filter(TrainingRecord.user_id == uid).all()
    if not recs:
        return pd.DataFrame(columns=["ID", "日付", "部位", "種目", "重量(kg)", "回数", "ボリューム"])
    return pd.DataFrame([{
        "ID": r.id,
        "日付": r.date,
        "部位": r.body_part,
        "種目": r.exercise,
        "重量(kg)": r.weight,
        "回数": r.reps,
        "ボリューム": r.volume
    } for r in recs])

# =========================
# ログインしていなければログイン画面へ
# =========================
if "user_uid" not in st.session_state:
    login_view()
    st.stop()

# =========================
# ログイン済み：アプリ本体
# =========================
st.title("🏋️‍♂️ AI Kintore：トレーニング分析ダッシュボード")
st.caption("📅 カレンダーで日付を選択 → 🏋️ 記録管理で編集・追加 → 📈 分析で推移を確認")
st.info(f"ログイン中：{st.session_state.get('user_email', '(email不明)')}")

df = load_df()

# =========================
# タブ構成
# =========================
tab_calendar, tab_manage, tab_analysis, tab_settings = st.tabs(
    ["📅 カレンダー", "🏋️ 記録管理", "📈 分析", "⚙️ 設定"]
)

# =========================
# 📅 カレンダー
# =========================
with tab_calendar:
    st.subheader("📅 トレーニングカレンダー")
    unique_dates = sorted(df["日付"].unique().tolist()) if not df.empty else []
    default_date = unique_dates[-1] if unique_dates else date.today()
    selected_date = st.date_input("日付を選択", value=default_date)
    st.session_state["selected_date"] = selected_date

    if selected_date in unique_dates:
        st.success(f"✅ {selected_date} の記録があります。")
    else:
        st.info(f"ℹ️ {selected_date} の記録はまだありません。")

    st.markdown("---")
    if df.empty:
        st.info("記録がまだありません。")
    else:
        df_copy = df.copy()
        df_copy["日付"] = pd.to_datetime(df_copy["日付"])
        df_copy["週"] = df_copy["日付"].dt.isocalendar().week
        df_copy["曜日"] = df_copy["日付"].dt.day_name(locale="ja_JP")
        df_copy["曜日"] = pd.Categorical(
            df_copy["曜日"],
            categories=["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"],
            ordered=True
        )
        heat_df = df_copy.groupby(["週", "曜日"])["ボリューム"].sum().reset_index()
        fig = px.density_heatmap(
            heat_df, x="週", y="曜日", z="ボリューム",
            color_continuous_scale="YlOrRd",
            labels={"ボリューム": "総ボリューム(kg)"},
            title="週間トレーニング負荷ヒートマップ"
        )
        fig.update_layout(height=400, margin=dict(l=30, r=30, t=50, b=30))
        st.plotly_chart(fig, use_container_width=True)

# =========================
# ⚙️ 設定・ログアウト
# =========================
with tab_settings:
    st.subheader("⚙️ 設定")
    if st.button("🚪 ログアウト"):
        st.session_state.clear()
        st.success("ログアウトしました。")
        st.rerun()

# =========================
# 📱 スマホ対応CSS
# =========================
st.markdown("""
<style>
[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
input, select, textarea { font-size: 16px !important; }
@media (max-width: 768px) { .stApp { zoom: 0.9; } }
</style>
""", unsafe_allow_html=True)

st.caption("AI Kintore v2.5 © 2025 | Firebase Admin Login + Cloud Compatible")
