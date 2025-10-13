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

# ===== Firebase (pyrebase) =====
import pyrebase

# -------------------------
# Firebase 設定（あなたの値を反映済み）
# -------------------------
firebaseConfig = {
    "apiKey": "AIzaSyBl9Te8OqO-vVdNWH8bK1Dj31D1IqrujZA",
    "authDomain": "ai-kintore.firebaseapp.com",
    "projectId": "ai-kintore",
    "storageBucket": "ai-kintore.firebasestorage.app",
    "messagingSenderId": "290962493885",
    "appId": "1:290962493885:web:b9353e2ce72a0ef9b742d4",
    "measurementId": "G-DP0F646EBL",
    # pyrebase が参照するため databaseURL を追加
    "databaseURL": "https://ai-kintore-default-rtdb.firebaseio.com",
}
firebase = pyrebase.initialize_app(firebaseConfig)
fb_auth = firebase.auth()

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
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("❌ .env に DATABASE_URL がありません。")
    st.stop()

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class TrainingRecord(Base):
    __tablename__ = "training_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 🔐 追加：ログインユーザー識別（必須）
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
st.set_page_config(page_title="AI Kintore v2.5 + Firebase Login", layout="wide")

session = SessionLocal()

# =========================
# ログインUI
# =========================
def login_view():
    st.title("🔐 ログイン / 新規登録（Firebase）")

    mode = st.radio("モードを選択", ["ログイン", "新規登録"], horizontal=True)
    email = st.text_input("📧 メールアドレス")
    password = st.text_input("🔑 パスワード", type="password")

    col_a, col_b = st.columns(2)
    if mode == "ログイン":
        if col_a.button("ログイン"):
            try:
                user = fb_auth.sign_in_with_email_and_password(email, password)
                st.session_state["user"] = user
                st.session_state["user_uid"] = user["localId"]
                st.session_state["user_email"] = email
                st.success(f"ようこそ {email} さん！")
                st.rerun()
            except Exception as e:
                st.error("ログインに失敗しました。メール/パスワードをご確認ください。")
    else:
        if col_b.button("新規登録"):
            try:
                fb_auth.create_user_with_email_and_password(email, password)
                st.success("✅ 登録完了！ログインしてください。")
            except Exception as e:
                st.error("登録に失敗しました。既に登録済みの可能性があります。")

# =========================
# 共通関数（※ユーザー別にフィルタ）
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

def validate_numeric_input(value: str, field_name: str):
    if not re.match(r'^[0-9]+(\.[0-9]+)?$', value.strip()):
        st.warning(f"⚠️ {field_name} は半角数字のみ入力可能です。")
        return None
    return float(value)

# =========================
# ルーティング（ログインしてなければログイン画面）
# =========================
if "user_uid" not in st.session_state:
    login_view()
    st.stop()

# =========================
# ログイン済み：アプリ本体
# =========================
st.title(f"🏋️‍♂️ AI Kintore：トレーニング分析ダッシュボード")
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
    selected_date = st.date_input("日付を選択", value=default_date, key="calendar_select")

    st.session_state["selected_date"] = selected_date

    if selected_date in unique_dates:
        st.success(f"✅ {selected_date} の記録があります。")
    else:
        st.info(f"ℹ️ {selected_date} の記録はまだありません。")

    st.markdown("---")
    st.markdown("### 🔥 トレーニング頻度ヒートマップ")

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
# 🏋️ 記録管理
# =========================
with tab_manage:
    selected_date = st.session_state.get("selected_date", date.today())
    st.header(f"🗓 {selected_date} の記録管理")

    daily_df = df[df["日付"] == selected_date] if not df.empty else pd.DataFrame(columns=df.columns)
    st.dataframe(
        daily_df[["部位", "種目", "重量(kg)", "回数", "ボリューム"]],
        use_container_width=True, hide_index=True
    )

    st.markdown("### ➕ 記録を追加")

    if "exercises" not in st.session_state:
        st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3}]

    for i, ex in enumerate(st.session_state.exercises):
        with st.expander(f"種目 {i+1}", expanded=True):
            c1, c2 = st.columns([1, 1])
            name = c1.text_input("種目名", value=ex["name"], key=f"name_{i}")
            part = c2.selectbox("部位", ["胸", "背中", "脚", "肩", "腕", "その他"], key=f"part_{i}")

            sets = st.number_input("セット数", min_value=1, max_value=10, value=int(ex["sets"]), key=f"sets_{i}")
            set_data = []
            for s in range(int(sets)):
                col_w, col_r = st.columns([1, 1])
                w = col_w.number_input(
                    f"第{s+1}セット 重量(kg)", min_value=0.0, max_value=500.0, step=2.5, key=f"w_{i}_{s}", format="%.1f"
                )
                r = col_r.number_input(
                    f"第{s+1}セット 回数", min_value=0, max_value=100, step=1, key=f"r_{i}_{s}"
                )
                set_data.append((w, r))
            ex["name"], ex["part"], ex["sets"], ex["data"] = name, part, sets, set_data

            if st.button("🗑️ この種目を削除", key=f"del_{i}"):
                st.session_state.exercises.pop(i)
                st.rerun()

    col1, col2 = st.columns(2)
    if col1.button("➕ 種目フォームを追加"):
        st.session_state.exercises.append({"name": "", "part": "胸", "sets": 3})
        st.rerun()

    if col2.button("💾 すべて保存"):
        new_records = []
        uid = st.session_state.get("user_uid")
        for ex in st.session_state.exercises:
            if not ex["name"]:
                continue
            for (w, r) in ex.get("data", []):
                if w > 0 and r > 0:
                    new_records.append(
                        TrainingRecord(
                            user_id=uid,
                            date=selected_date,
                            body_part=ex["part"],
                            exercise=ex["name"],
                            weight=w,
                            reps=r,
                            volume=w * r
                        )
                    )
        try:
            if new_records:
                session.add_all(new_records)
                session.commit()
                st.success("✅ 記録を保存しました。")
                st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3}]
                st.rerun()
            else:
                st.warning("⚠️ 入力内容を確認してください。")
        except Exception as e:
            session.rollback()
            st.error(f"❌ データベースエラー: {e}")

# =========================
# 📈 分析（回帰分析＋1RM）
# =========================
with tab_analysis:
    st.subheader("📈 部位→種目ごとの重量推移分析")

    if df.empty:
        st.info("記録がありません。")
    else:
        body_parts = df["部位"].unique().tolist()
        part_tabs = st.tabs(body_parts)
        for part_tab, part in zip(part_tabs, body_parts):
            with part_tab:
                part_df = df[df["部位"] == part]
                exercises = part_df["種目"].unique().tolist()
                ex_tabs = st.tabs(exercises)
                for ex_tab, ex in zip(ex_tabs, exercises):
                    with ex_tab:
                        ex_df = part_df[part_df["種目"] == ex]
                        if ex_df.empty:
                            st.info("記録なし")
                            continue

                        max_df = ex_df.groupby("日付")["重量(kg)"].max().reset_index()
                        if len(max_df) >= 2:
                            X = np.arange(len(max_df)).reshape(-1, 1)
                            y = max_df["重量(kg)"].values
                            model = LinearRegression().fit(X, y)
                            y_pred = model.predict(X)
                            next_pred = model.predict([[len(max_df)]])[0]
                            slope = model.coef_[0]
                        else:
                            y_pred = max_df["重量(kg)"].values
                            next_pred = None
                            slope = 0

                        ex_df["1RM"] = ex_df["重量(kg)"] * (1 + ex_df["回数"] / 30)
                        rm_df = ex_df.groupby("日付")["1RM"].max().reset_index()

                        fig, ax = plt.subplots(figsize=(8, 4))
                        sns.lineplot(data=max_df, x="日付", y="重量(kg)", marker="o", label="最大重量", ax=ax)
                        if len(max_df) >= 2:
                            sns.lineplot(x=max_df["日付"], y=y_pred, label="回帰予測", ax=ax, linestyle="--")
                        plt.xticks(rotation=45)
                        st.pyplot(fig, use_container_width=True)

                        fig2, ax2 = plt.subplots(figsize=(8, 3))
                        sns.lineplot(data=rm_df, x="日付", y="1RM", marker="s", color="orange", ax=ax2)
                        plt.xticks(rotation=45)
                        st.pyplot(fig2, use_container_width=True)

                        latest_row = ex_df.loc[ex_df["日付"].idxmax()]
                        c1, c2, c3 = st.columns(3)
                        c1.metric("🏋️ 最新最大重量", f"{latest_row['重量(kg)']} kg")
                        c2.metric("💪 最新1RM", f"{latest_row['1RM']:.1f} kg")
                        if next_pred:
                            trend = "📈 上昇" if slope > 0 else "📉 下降"
                            c3.metric(f"🔮 次回予測（傾向: {trend}）", f"{next_pred:.1f} kg")
                        else:
                            c3.metric("🔮 次回予測", "データ不足")

# =========================
# ⚙️ 設定・バックアップ
# =========================
with tab_settings:
    st.subheader("⚙️ 設定・バックアップ")

    # 接続確認
    try:
        conn = engine.connect()
        st.success("✅ データベース接続成功")
        conn.close()
    except Exception as e:
        st.error(f"❌ データベース接続に失敗しました: {e}")

    # バックアップ（自分のデータのみ）
    st.markdown("### 💾 バックアップ（CSV）")
    if df.empty:
        st.info("データがまだありません。")
    else:
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        st.download_button(
            label="📥 CSVをダウンロード",
            data=buffer.getvalue(),
            file_name=f"training_backup_{date.today()}.csv",
            mime="text/csv"
        )

    # 復元（アップロードしたデータを現在のユーザーで保存）
    st.markdown("### 📤 CSVから復元")
    uploaded = st.file_uploader("CSVファイルを選択", type=["csv"])
    if uploaded:
        try:
            new_df = pd.read_csv(uploaded)
            new_df["日付"] = pd.to_datetime(new_df["日付"]).dt.date
            uid = st.session_state.get("user_uid")
            records = [
                TrainingRecord(
                    user_id=uid,
                    date=row["日付"],
                    body_part=row["部位"],
                    exercise=row["種目"],
                    weight=row["重量(kg)"],
                    reps=row["回数"],
                    volume=row["ボリューム"]
                )
                for _, row in new_df.iterrows()
            ]
            session.add_all(records)
            session.commit()
            st.success(f"✅ {len(records)}件の記録を復元しました。")
        except Exception as e:
            session.rollback()
            st.error(f"❌ 復元エラー: {e}")

    st.markdown("---")
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

st.caption("AI Kintore v2.5 © 2025 | Firebase Login + User-scoped data")
