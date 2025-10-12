# app.py
# ─────────────────────────────────────────────────────────────────────────────
# 筋トレ成果トラッカー × データ分析（Streamlit単一ファイル版）
# - CSVアップロード or その場入力
# - コンパクトUI（data_editor採用）
# - 週次総ボリューム / 種目別ボリューム / 頻度ヒートマップ / 種目別PR推移
# - 日本語フォントの文字化け対策
# 必要: pip install streamlit pandas matplotlib scikit-learn
# ─────────────────────────────────────────────────────────────────────────────

import io
import sys
import math
import datetime as dt
from typing import List

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
import matplotlib
import matplotlib.pyplot as plt

# ── 文字化け対策: 利用可能な日本語フォントを優先設定 ─────────────────────────────
def set_ja_font():
    candidates = [
        "Noto Sans CJK JP", "Noto Sans JP", "IPAexGothic",
        "Yu Gothic", "Meiryo", "Hiragino Sans", "TakaoPGothic",
        "DejaVu Sans"  # 最後の砦
    ]
    avail = set(f.name for f in matplotlib.font_manager.fontManager.ttflist)
    for name in candidates:
        if name in avail:
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return name
    # 何も見つからない場合も DejaVu Sans で継続
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return "DejaVu Sans"

FONT_USED = set_ja_font()

# ── ページ設定 ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="筋トレ成果トラッカー", page_icon="💪", layout="wide")

# ── ヘッダー ────────────────────────────────────────────────────────────────
st.title("💪 筋トレ成果トラッカー × データ分析（プロトタイプ）")
st.caption(
    "CSVをアップロードするかフォームで入力すると、週次推移・種目別ボリューム・頻度ヒートマップ・PR推移を自動可視化します。"
)
st.info(
    "想定CSV列: `date, exercise, weight, reps` （必要なら `bodypart` 追加可）\n"
    "・`date`は YYYY-MM-DD or YYYY/MM/DD\n"
    "・総ボリューム = weight × reps（セット数は行を分けて入力）",
    icon="📄"
)

# ── サイドバー（入力） ───────────────────────────────────────────────────────
st.sidebar.header("📥 データ入力")

uploaded = st.sidebar.file_uploader(
    "training_log.csv をアップロード（任意）", type=["csv"]
)

def read_csv_with_fallback(file) -> pd.DataFrame:
    content = file.read()
    for enc in ["utf-8-sig", "utf-8", "cp932"]:
        try:
            return pd.read_csv(io.BytesIO(content), encoding=enc)
        except Exception:
            continue
    return pd.read_csv(io.BytesIO(content))  # どうしても無理なら標準

df_csv = None
if uploaded:
    try:
        df_csv = read_csv_with_fallback(uploaded)
        st.sidebar.success("CSVを読み込みました ✅")
    except Exception as e:
        st.sidebar.error(f"CSV読込エラー: {e}")

st.sidebar.markdown("---")

# ── その場入力（コンパクトUI） ──────────────────────────────────────────────
st.subheader("📝 今日の記録を素早く追加（コンパクト入力）")

with st.expander("入力フォームを開く／閉じる", expanded=True):
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        input_date = st.date_input("日付", value=dt.date.today())
    with c2:
        num_ex = st.number_input("種目数", min_value=1, max_value=10, value=2, step=1)
    with c3:
        _ = st.text_input("（任意）今日のメモ", value="", key="note")

    st.caption("下の表に **weight(kg)** と **reps(回)** を1セットごとに記録してください。行＝セット。")

    exercises: List[pd.DataFrame] = []
    names: List[str] = []

    for i in range(int(num_ex)):
        st.markdown(f"**🏋️ 種目{i+1}**")
        ncol1, ncol2 = st.columns([2, 1])
        with ncol1:
            ex_name = st.text_input(f"種目名 - {i+1}", value="ベンチプレス" if i == 0 else "", key=f"ex_{i}")
        with ncol2:
            bodypart = st.selectbox(
                f"部位 - {i+1}",
                ["胸", "背中", "脚", "肩", "腕", "体幹", "その他"],
                index=0 if i == 0 else 6,
                key=f"bp_{i}",
            )
        default_df = pd.DataFrame({"weight": [60, 70, 80][:1], "reps": [10, 8, 6][:1]})
        edit_df = st.data_editor(
            default_df,
            key=f"tbl_{i}",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "weight": st.column_config.NumberColumn("重量(kg)", min_value=0, step=2),
                "reps": st.column_config.NumberColumn("回数", min_value=0, step=1),
            },
        )
        if ex_name.strip():
            tmp = edit_df.copy()
            tmp["exercise"] = ex_name.strip()
            tmp["bodypart"] = bodypart
            tmp["date"] = pd.to_datetime(str(input_date))
            exercises.append(tmp)
            names.append(ex_name.strip())

    df_input = pd.concat(exercises, ignore_index=True) if exercises else pd.DataFrame()

# ── データ結合・整形 ──────────────────────────────────────────────────────────
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    # 列名のゆらぎを吸収
    col_map = {c.lower().strip(): c for c in df.columns}
    # 必須列チェック
    for need in ["date", "exercise", "weight", "reps"]:
        if need not in [c.lower().strip() for c in df.columns]:
            raise ValueError(f"CSVに必要な列 `{need}` が見つかりません。現在の列: {list(df.columns)}")
    # 正規化
    df["date"] = pd.to_datetime(df[col_map.get("date", "date")])
    df["exercise"] = df[col_map.get("exercise", "exercise")].astype(str)
    df["weight"] = pd.to_numeric(df[col_map.get("weight", "weight")], errors="coerce").fillna(0)
    df["reps"] = pd.to_numeric(df[col_map.get("reps", "reps")], errors="coerce").fillna(0).astype(int)
    if "bodypart" in [c.lower().strip() for c in df.columns]:
        df["bodypart"] = df[col_map.get("bodypart", "bodypart")].astype(str)
    else:
        df["bodypart"] = "その他"
    df["volume"] = df["weight"] * df["reps"]
    df = df.sort_values("date")
    return df[["date", "exercise", "bodypart", "weight", "reps", "volume"]]

df_all_list = []
if df_csv is not None:
    try:
        df_all_list.append(normalize(df_csv))
    except Exception as e:
        st.error(f"CSV整形エラー: {e}")

if not df_input.empty:
    df_all_list.append(normalize(df_input))

df_all = pd.concat(df_all_list, ignore_index=True) if df_all_list else pd.DataFrame(
    columns=["date", "exercise", "bodypart", "weight", "reps", "volume"]
)

# ── 概要メトリクス ───────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 サマリー")

if df_all.empty:
    st.warning("データがありません。CSVをアップロードするか、上のフォームに入力してください。")
else:
    # 週次の集計
    df_all["week"] = df_all["date"].dt.to_period("W").apply(lambda p: p.start_time.date())
    this_week = df_all[df_all["week"] == df_all["week"].max()]
    last_week = df_all[df_all["week"] == (df_all["week"].max() - dt.timedelta(days=7))]

    total_vol = int(df_all["volume"].sum())
    week_vol = int(this_week["volume"].sum())
    last_vol = int(last_week["volume"].sum()) if not last_week.empty else 0
    diff = week_vol - last_vol
    diff_pct = (diff / last_vol * 100) if last_vol > 0 else np.nan

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("総ボリューム（累計）", f"{total_vol:,}")
    m2.metric("今週のボリューム", f"{week_vol:,}", delta=(f"{diff:+,}" if not math.isnan(diff) else None))
    m3.metric("種目数", df_all["exercise"].nunique())
    m4.metric("日本語フォント", FONT_USED)

    st.dataframe(df_all, use_container_width=True, height=260)

# ── 可視化（4点） ────────────────────────────────────────────────────────────
if not df_all.empty:
    st.markdown("### 📈 1) 週ごとの総ボリューム推移")
    fig1, ax1 = plt.subplots(figsize=(8, 3.6))
    weekly = df_all.groupby(df_all["date"].dt.to_period("W"))["volume"].sum()
    weekly.index = weekly.index.to_timestamp()  # Period→Timestamp
    ax1.plot(weekly.index, weekly.values, marker="o")
    ax1.set_xlabel("週")
    ax1.set_ylabel("総ボリューム")
    ax1.set_title("週ごとの総ボリューム推移")
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1, use_container_width=True)

    st.markdown("### 🏋️ 2) 種目別トータルボリューム（ランキング）")
    fig2, ax2 = plt.subplots(figsize=(8, 3.6))
    by_ex = df_all.groupby("exercise")["volume"].sum().sort_values(ascending=True)
    ax2.barh(by_ex.index, by_ex.values)
    ax2.set_xlabel("総ボリューム")
    ax2.set_title("種目別トータルボリューム")
    for i, v in enumerate(by_ex.values):
        ax2.text(v, i, f" {int(v):,}", va="center")
    st.pyplot(fig2, use_container_width=True)

    st.markdown("### 📅 3) トレーニング頻度ヒートマップ（週×曜日）")
    # 週×曜日の回数をピボット
    tmp = df_all.copy()
    tmp["week_start"] = tmp["date"].dt.to_period("W").apply(lambda p: p.start_time.date())
    tmp["weekday"] = tmp["date"].dt.weekday  # 0=Mon .. 6=Sun
    pivot = tmp.pivot_table(index="week_start", columns="weekday", values="exercise", aggfunc="count", fill_value=0)
    # 表示を見やすく（日→土のラベル）
    wd_labels = ["月", "火", "水", "木", "金", "土", "日"]
    fig3, ax3 = plt.subplots(figsize=(8, 3.6))
    im = ax3.imshow(pivot.values, aspect="auto")
    ax3.set_yticks(range(len(pivot.index)))
    ax3.set_yticklabels([str(d) for d in pivot.index])
    ax3.set_xticks(range(7))
    ax3.set_xticklabels(wd_labels)
    ax3.set_xlabel("曜日")
    ax3.set_ylabel("週（開始日）")
    ax3.set_title("トレーニング頻度（セッション数）")
    # 値を上に描く
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            ax3.text(j, i, pivot.values[i, j], ha="center", va="center", color="white" if pivot.values[i, j] >= np.max(pivot.values)/2 else "black")
    fig3.colorbar(im, ax=ax3, fraction=0.046, pad=0.04)
    st.pyplot(fig3, use_container_width=True)

    st.markdown("### 🏆 4) 種目別PR（最大重量）推移")
    # 種目選択
    choices = sorted(df_all["exercise"].unique())
    default_idx = 0
    ex_sel = st.selectbox("種目を選択", choices, index=default_idx if choices else None, key="pr_sel")

    if ex_sel:
        ex_df = df_all[df_all["exercise"] == ex_sel].copy()
        # 日ごとの最大重量を採用
        pr_daily = ex_df.groupby(ex_df["date"].dt.date)["weight"].max().reset_index()
        pr_daily = pr_daily.sort_values("date")
        X = np.arange(len(pr_daily)).reshape(-1, 1)
        y = pr_daily["weight"].values
        fig4, ax4 = plt.subplots(figsize=(8, 3.6))
        ax4.plot(pr_daily["date"], y, marker="o", label="日別最大重量")
        # トレンドライン
        if len(pr_daily) >= 2:
            model = LinearRegression().fit(X, y)
            y_hat = model.predict(X)
            ax4.plot(pr_daily["date"], y_hat, linestyle="--", label="トレンド")
            slope = model.coef_[0]
            st.caption(f"➡️ 伸び率推定: 1セッションあたり **{slope:.2f} kg** の上昇ペース")
        ax4.set_title(f"{ex_sel} の最大重量推移（PRトラッキング）")
        ax4.set_xlabel("日付")
        ax4.set_ylabel("重量(kg)")
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        st.pyplot(fig4, use_container_width=True)

# ── フッター ───────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("© 筋トレ成果トラッカー Prototype — pandas / matplotlib / Streamlit / scikit-learn")
