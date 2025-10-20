# ================================================
# 🏋️ AI Kintore - UIアップデート v5.4
# ✅ 横並び・固定ナビバー
# ✅ ログイン維持
# ✅ SPA式切り替え
# ================================================
import os
import platform
from datetime import date
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import bcrypt
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import Column, Date, Float, Integer, String, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from matplotlib import font_manager

# =========================
# Streamlit設定
# =========================
st.set_page_config(page_title="AI Kintore", layout="wide")

# =========================
# CSSスタイル
# =========================
st.markdown("""
<style>
body { background-color: #fafafa; }

/* ページ余白 */
.block-container {
  max-width: 950px;
  margin: 5rem auto 0 auto;
  padding-top: 1.5rem;
}

/* ナビバー */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background-color: #1E1E1E;
  color: white;
  padding: 12px 30px;
  border-bottom: 2px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 9999;
}
.navbar-title {
  font-weight: bold;
  font-size: 18px;
  color: #fff;
}
.navbar-menu {
  display: flex;
  gap: 20px;
}
.navbar-menu button {
  background: transparent !important;
  border: none !important;
  color: #bbb !important;
  font-weight: bold;
  font-size: 15px;
  cursor: pointer;
}
.navbar-menu button:hover { color: white !important; text-decoration: underline; }
.navbar-menu button.active { color: #FFD700 !important; }

h1, h2, h3 { color: #0078D7; }

.stButton>button {
  background-color: #0078D7;
  color: white;
  border-radius: 8px;
  font-weight: bold;
}
.stButton>button:hover { background-color: #005a9e; }

.card {
  background-color: #f9f9f9;
  padding: 15px 20px;
  margin-bottom: 10px;
  border-radius: 10px;
  box-shadow: 1px 1px 8px rgba(0,0,0,0.1);
}
.card-title { font-weight: bold; color: #333; font-size: 1.1rem; }
.card-sub { color: #666; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

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
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "ipaexg.ttf")
        if os.path.exists(font_path):
            font_manager.fontManager.addfont(font_path)
            font_name = "IPAexGothic"
        else:
            font_name = "DejaVu Sans"
    plt.rcParams["font.family"] = font_name
    sns.set(font=font_name, style="whitegrid")

set_japanese_font()

# =========================
# DB設定
# =========================
DATABASE_URL = st.secrets.get("DATABASE_URL", None)
if not DATABASE_URL:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("❌ DATABASE_URL が見つかりません。")
    st.stop()

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
session = SessionLocal()

# =========================
# モデル定義
# =========================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

class TrainingRecord(Base):
    __tablename__ = "training_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    body_part = Column(String, index=True, nullable=False)
    exercise = Column(String, index=True, nullable=False)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    volume = Column(Float, nullable=False)

Base.metadata.create_all(bind=engine)

# =========================
# 認証関連
# =========================
import bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# =========================
# ログイン・サインアップ
# =========================
def login_view():
    st.title("🔐 ログイン")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        user = session.query(User).filter_by(email=email).first()
        if user and verify_password(password, user.password_hash):
            st.session_state["user_id"] = user.id
            st.session_state["user_email"] = user.email
            st.session_state["active_tab"] = "calendar"
            st.rerun()
        else:
            st.error("メールアドレスまたはパスワードが正しくありません。")

    if st.button("🆕 新規登録はこちら"):
        st.session_state["mode"] = "signup"
        st.rerun()

def signup_view():
    st.title("🆕 新規登録")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")
    if st.button("登録"):
        if session.query(User).filter_by(email=email).first():
            st.error("このメールアドレスは既に登録済みです。")
        else:
            user = User(email=email, password_hash=hash_password(password))
            session.add(user)
            session.commit()
            st.success("✅ 登録完了！ログインしてください。")
            st.session_state["mode"] = "login"
            st.rerun()

# =========================
# ログイン維持チェック
# =========================
if "mode" not in st.session_state:
    st.session_state["mode"] = "login"

if "user_id" not in st.session_state:
    if st.session_state["mode"] == "login":
        login_view()
    else:
        signup_view()
    st.stop()

# =========================
# タブ初期化
# =========================
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "calendar"

# =========================
# 固定ナビバー
# =========================
tabs = {
    "calendar": "📅 カレンダー",
    "record": "🏋️ 記録管理",
    "edit": "✏️ 編集",
    "analysis": "📈 分析",
    "settings": "⚙️ 設定"
}

st.markdown(
    '<div class="navbar">'
    '<div class="navbar-title">🏋️ AI Kintore</div>'
    '<div class="navbar-menu">',
    unsafe_allow_html=True,
)

cols = st.columns(len(tabs))
for i, (key, label) in enumerate(tabs.items()):
    with cols[i]:
        if st.button(label, key=f"nav_{key}"):
            st.session_state["active_tab"] = key
            st.rerun()
        if st.session_state["active_tab"] == key:
            st.markdown(
                f"<script>document.querySelectorAll('.stButton button')[{i}].classList.add('active');</script>",
                unsafe_allow_html=True,
            )

st.markdown("</div></div>", unsafe_allow_html=True)
st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# =========================
# データ取得
# =========================
def load_df():
    uid = st.session_state["user_id"]
    recs = session.query(TrainingRecord).filter_by(user_id=uid).order_by(TrainingRecord.date.asc()).all()
    return pd.DataFrame([{
        "ID": r.id, "日付": r.date, "部位": r.body_part, "種目": r.exercise,
        "重量(kg)": r.weight, "回数": r.reps, "ボリューム": r.volume
    } for r in recs])

df = load_df()
active_tab = st.session_state["active_tab"]

# =========================
# 各画面内容
# =========================
st.title(f"🏋️‍♂️ AI Kintore - {st.session_state['user_email']} さん")

# --- カレンダー ---
if active_tab == "calendar":
    if not df.empty:
        df_copy = df.copy()
        df_copy["日付"] = pd.to_datetime(df_copy["日付"])
        df_copy["週"] = df_copy["日付"].dt.isocalendar().week
        try:
            df_copy["曜日"] = df_copy["日付"].dt.day_name(locale="ja_JP")
        except Exception:
            df_copy["曜日"] = df_copy["日付"].dt.day_name()
        heat_df = df_copy.groupby(["週", "曜日"])["ボリューム"].sum().reset_index()
        fig = px.density_heatmap(
            heat_df, x="週", y="曜日", z="ボリューム",
            color_continuous_scale="YlOrRd", title="週ごと・曜日ごとの総ボリューム分布"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("まだトレーニング記録がありません。")

# --- 記録管理 ---
elif active_tab == "record":
    st.subheader("🏋️ トレーニング記録の追加")
    selected_date = st.date_input("日付を選択", value=date.today())
    st.session_state["selected_date"] = selected_date

    if "exercises" not in st.session_state:
        st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3, "data": []}]

    col_add, col_reset = st.columns(2)
    if col_add.button("＋ 種目を追加"):
        st.session_state.exercises.append({"name": "", "part": "胸", "sets": 3, "data": []})
    if col_reset.button("🗑 全てクリア"):
        st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3, "data": []}]

    for i, ex in enumerate(st.session_state.exercises):
        with st.expander(f"種目 {i+1}", expanded=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input("種目名", value=ex["name"], key=f"name_{i}")
            part = c2.selectbox("部位", ["胸", "背中", "脚", "肩", "腕", "その他"], key=f"part_{i}")
            sets = c3.number_input("セット数", 1, 10, value=int(ex.get("sets", 3)), key=f"sets_{i}")
            set_data = []
            for s in range(int(sets)):
                cw, cr = st.columns(2)
                w = cw.number_input(f"第{s+1}セット 重量(kg)", 0.0, 500.0, step=2.5, key=f"w_{i}_{s}")
                r = cr.number_input(f"第{s+1}セット 回数", 0, 100, step=1, key=f"r_{i}_{s}")
                set_data.append((w, r))
            ex.update({"name": name, "part": part, "sets": sets, "data": set_data})

    if st.button("💾 保存"):
        uid = st.session_state["user_id"]
        new_records = []
        for ex in st.session_state.exercises:
            for (w, r) in ex["data"]:
                if w > 0 and r > 0:
                    new_records.append(TrainingRecord(
                        user_id=uid, date=selected_date,
                        body_part=ex["part"], exercise=ex["name"],
                        weight=w, reps=r, volume=w*r
                    ))
        if new_records:
            session.add_all(new_records)
            session.commit()
            st.success("✅ 保存しました！")
            st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3, "data": []}]
            st.rerun()
        else:
            st.info("入力がありません。")

# --- 編集 ---
elif active_tab == "edit":
    st.subheader("✏️ 記録の編集 / 削除")
    selected_date = st.date_input("📅 編集・削除する日付を選択", value=date.today(), key="edit_date")
    records = session.query(TrainingRecord).filter_by(user_id=st.session_state["user_id"], date=selected_date).all()

    if not records:
        st.info("この日には記録がありません。")
    else:
        for r in records:
            st.markdown(f"<div class='card'><div class='card-title'>{r.body_part} - {r.exercise}</div>"
                        f"<div class='card-sub'>{r.weight}kg × {r.reps}回　Volume: {r.volume}</div></div>",
                        unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("✏️ 編集", key=f"edit_{r.id}"):
                st.session_state["edit_target"] = r.id
            if c2.button("🗑 削除", key=f"del_{r.id}"):
                session.delete(r)
                session.commit()
                st.success(f"削除しました: {r.exercise}")
                st.rerun()

        if "edit_target" in st.session_state:
            target = session.get(TrainingRecord, st.session_state["edit_target"])
            st.markdown("---")
            st.markdown(f"### ✏️ {target.exercise} を編集")
            new_weight = st.number_input("重量(kg)", value=target.weight)
            new_reps = st.number_input("回数", value=target.reps)
            if st.button("保存"):
                target.weight = new_weight
                target.reps = new_reps
                target.volume = new_weight * new_reps
                session.commit()
                st.success("✅ 更新しました！")
                del st.session_state["edit_target"]
                st.rerun()

# --- 分析 ---
elif active_tab == "analysis":
    st.subheader("📈 部位別・種目別の推移")
    if df.empty:
        st.info("データがありません。")
    else:
        # --- 部位ごとにタブを分ける ---
        body_parts = df["部位"].unique().tolist()
        part_tabs = st.tabs(body_parts)

        for tab, part in zip(part_tabs, body_parts):
            with tab:
                part_df = df[df["部位"] == part]
                st.markdown(f"### 🏋️‍♂️ {part} の推移")

                exercises = part_df["種目"].unique().tolist()
                if not exercises:
                    st.info("この部位の記録はまだありません。")
                    continue

                # --- 種目ごとの折れ線グラフ ---
                for ex in exercises:
                    ex_df = part_df[part_df["種目"] == ex].sort_values("日付")
                    if ex_df.empty:
                        continue
                    fig, ax = plt.subplots(figsize=(6, 3))
                    sns.lineplot(data=ex_df, x="日付", y="重量(kg)", marker="o", ax=ax)
                    ax.set_title(f"{ex} の推移", fontsize=12)
                    ax.set_xlabel("日付")
                    ax.set_ylabel("重量(kg)")
                    st.pyplot(fig, use_container_width=True)


# --- 設定 ---
elif active_tab == "settings":
    st.subheader("⚙️ アカウント設定")
    st.write(f"ログイン中: {st.session_state['user_email']}")
    if st.button("🚪 ログアウト"):
        st.session_state.clear()
        st.success("ログアウトしました。")
        st.rerun()
