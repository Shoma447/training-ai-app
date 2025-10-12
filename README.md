# 💪 筋トレ成果トラッカー × データ分析アプリ

Streamlit × FastAPI × pandas で構築する、  
「トレーニング記録をデータで見える化」する個人開発プロジェクト。

---

## 🧠 プロジェクト概要
ユーザーがトレーニングログ（例：`training_log.csv`）をアップロードすると、  
アプリが自動で統計・グラフ・AI分析を行い、自身の成長をデータで可視化します。

---

## 🧩 技術スタック
| 分類 | 使用技術 |
|------|-----------|
| フロントエンド | Streamlit |
| バックエンド | FastAPI（今後統合予定） |
| データ分析 | pandas / matplotlib / scikit-learn |
| 言語 | Python 3.11 |
| 環境管理 | venv |
| バージョン管理 | Git + GitHub Flow |

---

## 📊 主な機能
- CSVアップロード / その場入力
- 週ごとの総トレーニングボリューム推移グラフ
- 種目別トータルボリュームランキング
- トレーニング頻度ヒートマップ（週×曜日）
- 種目別PR（最大重量）推移＋回帰トレンド分析
- 日本語フォント自動対応（文字化け防止）

---

## 🏗️ ディレクトリ構成（予定）
training-ai-app/
├── backend_fastapi/
│ ├── app/
│ │ ├── main.py # APIエントリ
│ │ └── routes/ # CRUD関連
│ └── requirements.txt
├── frontend_streamlit/
│ ├── app.py # Streamlitアプリ本体
│ └── requirements.txt
└── README.md

yaml
コードをコピーする

---

## 🚀 実行方法
```bash
# 仮想環境の作成
python -m venv venv
.\venv\Scripts\activate    # Windowsの場合

# 依存パッケージのインストール
pip install -r frontend_streamlit/requirements.txt

# Streamlitアプリ起動
cd frontend_streamlit
streamlit run app.py
🧪 今後のロードマップ
 FastAPIと連携してトレーニングデータを保存

 ユーザー認証（Firebase Authentication）

 Docker対応（ローカル再現性向上）

 AIコメント生成機能（「ベンチ伸びてますね🔥」など）

 月次レポートPDF出力

🧑‍💻 開発ルール（GitHub Flow）
mainブランチは保護（直接push禁止）

feature/* ブランチで開発

PR作成 → レビュー → mainにマージ

📜 ライセンス
MIT License

yaml
コードをコピーする

---

### 💡補足
- このREADMEを **`main`ブランチに直接追加せず**、  
  できれば **`feature/add-readme`** ブランチを作ってコミット → PR するのが理想です。
  ```bash
  git checkout -b feature/add-readme
  git add README.md
  git commit -m "docs: add initial README"
  git push origin feature/add-readme
その後、GitHubで main に向けてPRを作成。
