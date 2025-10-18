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
from sklearn.linear_model import LinearRegression
from sqlalchemy import Column, Date, Float, Integer, String, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# =========================
# Streamlit 基本設定
# =========================
st.set_page_config(page_title="AI Kintore", layout="wide")
# =========================
# 日本語フォント設定（Streamlit Cloud対応）
# =========================
def set_japanese_font():
    os_name = platform.system()
    if os_name == "Windows":
        font_name = "Meiryo"
    elif os_name == "Darwin":  # macOS
        font_name = "Hiragino Maru Gothic Pro"
    else:
        # ✅ Linux (Streamlit Cloudなど)
        font_name = "IPAexGothic"
        font_path = "/usr/share/fonts/truetype/ipafont-gothic/ipagp.ttf"

        # フォントが無ければ自動インストール
        if not os.path.exists(font_path):
            os.system("apt-get update -y && apt-get install -y fonts-ipafont-gothic")

    plt.rcParams["font.family"] = font_name
    sns.set(font=font_name, style="whitegrid")

set_japanese_font()


# =========================
# DB接続設定（Cloud/Local両対応）
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
# パスワード関連関数
# =========================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# =========================
# 認証画面
# =========================
def login_view():
    st.title("🔐 ログイン")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        if not email or not password:
            st.error("メールアドレスとパスワードを入力してください。")
        else:
            user = session.query(User).filter_by(email=email).first()
            if user and verify_password(password, user.password_hash):
                st.session_state["user_id"] = user.id
                st.session_state["user_email"] = user.email
                st.success(f"ようこそ {user.email} さん！")
                st.rerun()
            else:
                st.error("メールアドレスまたはパスワードが正しくありません。")

    st.markdown("---")
    if st.button("🆕 新規登録はこちら"):
        st.session_state["mode"] = "signup"
        st.rerun()

def signup_view():
    st.title("🆕 新規登録")
    email = st.text_input("メールアドレス")
    password = st.text_input("パスワード（8文字以上推奨）", type="password")

    if st.button("登録"):
        if not email or not password:
            st.error("メールアドレスとパスワードを入力してください。")
        elif session.query(User).filter_by(email=email).first():
            st.error("このメールアドレスはすでに登録されています。")
        else:
            try:
                user = User(email=email, password_hash=hash_password(password))
                session.add(user)
                session.commit()
                st.success("✅ 登録完了！ログインしてください。")
                st.session_state["mode"] = "login"
                st.rerun()
            except Exception as e:
                session.rollback()
                st.error(f"登録エラー: {e}")

# =========================
# ログイン状態チェック
# =========================
if "mode" not in st.session_state:
    st.session_state["mode"] = "login"

if "user_id" not in st.session_state:
    if st.session_state["mode"] == "login":
        login_view()
    elif st.session_state["mode"] == "signup":
        signup_view()
    st.stop()

# =========================
# DBロード関数
# =========================
def load_df():
    uid = st.session_state.get("user_id")
    if not uid:
        return pd.DataFrame(columns=["ID", "日付", "部位", "種目", "重量(kg)", "回数", "ボリューム"])
    recs = session.query(TrainingRecord).filter_by(user_id=uid).order_by(TrainingRecord.date.asc()).all()
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
# 本体UI
# =========================
st.title(f"🏋️‍♂️ AI Kintore - {st.session_state['user_email']} さんのダッシュボード")

df = load_df()

tab1, tab2, tab3, tab4 = st.tabs(["📅 カレンダー", "🏋️ 記録管理", "📈 分析", "⚙️ 設定"])

# 📅 カレンダー
with tab1:
    st.subheader("📅 トレーニングカレンダー")

    if not df.empty:
        df_copy = df.copy()
        df_copy["日付"] = pd.to_datetime(df_copy["日付"])
        df_copy["週"] = df_copy["日付"].dt.isocalendar().week

        # ✅ 日本語ロケールが使えない環境対策
        try:
            df_copy["曜日"] = df_copy["日付"].dt.day_name(locale="ja_JP")
        except Exception:
            df_copy["曜日"] = df_copy["日付"].dt.day_name()  # fallback to English

        # ✅ ヒートマップ作成
        heat_df = df_copy.groupby(["週", "曜日"])["ボリューム"].sum().reset_index()
        fig = px.density_heatmap(
            heat_df,
            x="週",
            y="曜日",
            z="ボリューム",
            color_continuous_scale="YlOrRd",
            labels={"ボリューム": "総ボリューム(kg)", "週": "週番号", "曜日": "曜日"},
            title="週ごと・曜日ごとの総ボリューム分布"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🟡 赤いほどその週・曜日のトレーニングボリュームが高いことを示します。")
    else:
        st.info("まだトレーニング記録がありません。")


# 🏋️ 記録管理
with tab2:
    st.subheader("🏋️ トレーニング記録の追加/一覧")

    selected_date = st.date_input("日付を選択", value=date.today())
    st.session_state["selected_date"] = selected_date

    show_df = df[df["日付"] == selected_date] if not df.empty else pd.DataFrame(columns=df.columns)
    st.caption(f"📅 対象日: {selected_date}")
    st.dataframe(show_df, use_container_width=True, hide_index=True)

    st.markdown("### ➕ 記録追加")

    if "exercises" not in st.session_state:
        st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3, "data": []}]

    col_add, col_clear = st.columns([1, 1])
    if col_add.button("＋ 種目を追加"):
        st.session_state.exercises.append({"name": "", "part": "胸", "sets": 3, "data": []})
    if col_clear.button("🗑 種目を全てクリア"):
        st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3, "data": []}]

    for i, ex in enumerate(st.session_state.exercises):
        with st.expander(f"種目 {i+1}", expanded=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input("種目名", value=ex["name"], key=f"name_{i}")
            part = c2.selectbox("部位", ["胸", "背中", "脚", "肩", "腕", "その他"], key=f"part_{i}")
            sets = c3.number_input("セット数", min_value=1, max_value=10, value=int(ex.get("sets", 3)), key=f"sets_{i}")

            set_data = []
            for s in range(int(sets)):
                cw, cr = st.columns(2)
                w = cw.number_input(f"第{s+1}セット 重量(kg)", min_value=0.0, max_value=500.0, step=2.5, key=f"w_{i}_{s}")
                r = cr.number_input(f"第{s+1}セット 回数", min_value=0, max_value=100, step=1, key=f"r_{i}_{s}")
                set_data.append((w, r))
            ex.update({"name": name, "part": part, "sets": sets, "data": set_data})

            if st.button(f"この種目を削除", key=f"del_ex_{i}"):
                st.session_state.exercises.pop(i)
                st.rerun()

    if st.button("💾 保存"):
        try:
            uid = st.session_state["user_id"]
            new_records = []
            for ex in st.session_state.exercises:
                if not ex["name"]:
                    continue
                for (w, r) in ex["data"]:
                    if w > 0 and r > 0:
                        new_records.append(TrainingRecord(
                            user_id=uid,
                            date=selected_date,
                            body_part=ex["part"],
                            exercise=ex["name"],
                            weight=float(w),
                            reps=int(r),
                            volume=float(w) * int(r)
                        ))
            if new_records:
                session.add_all(new_records)
                session.commit()
                st.success("✅ 保存しました。")
                st.session_state.exercises = [{"name": "", "part": "胸", "sets": 3, "data": []}]
                st.rerun()
            else:
                st.info("入力がありません。重量・回数を1以上で入力してください。")
        except Exception as e:
            session.rollback()
            st.error(f"記録保存エラー: {e}")

# 📈 分析
with tab3:
    st.subheader("📈 部位・種目別分析")

    if df.empty:
        st.info("記録がまだありません。")
    else:
        body_parts = df["部位"].unique().tolist()
        part_tabs = st.tabs(body_parts)

        for part_tab, part in zip(part_tabs, body_parts):
            with part_tab:
                part_df = df[df["部位"] == part]

                for ex in part_df["種目"].unique():
                    st.markdown(f"#### 🏋️ {ex}")
                    ex_df = part_df[part_df["種目"] == ex].copy()
                    ex_df["日付"] = pd.to_datetime(ex_df["日付"])

                    # 日別最大重量
                    max_df = ex_df.groupby("日付")["重量(kg)"].max().reset_index()

                    # ✅ グラフ生成
                    fig, ax = plt.subplots(figsize=(8, 3))
                    sns.lineplot(x=max_df["日付"], y=max_df["重量(kg)"], ax=ax, marker="o", label="実績")

                    if len(max_df) >= 2:
                        X = np.arange(len(max_df)).reshape(-1, 1)
                        y = max_df["重量(kg)"].values
                        model = LinearRegression().fit(X, y)
                        y_pred = model.predict(X)
                        sns.lineplot(x=max_df["日付"], y=y_pred, ax=ax, linestyle="--", label="トレンド")

                    ax.set_xlabel("日付")
                    ax.set_ylabel("最大重量(kg)")
                    ax.set_title(f"{ex} の挙上重量推移")
                    ax.legend()
                    st.pyplot(fig, use_container_width=True)

# ⚙️ 設定
with tab4:
    st.subheader("⚙️ アカウント設定")
    st.write(f"ログイン中: {st.session_state['user_email']}")
    if st.button("🚪 ログアウト"):
        st.session_state.clear()
        st.success("ログアウトしました。")
        st.rerun()

st.caption("AI Kintore v3.1 © 2025 | Local Auth + DB + Analysis")
