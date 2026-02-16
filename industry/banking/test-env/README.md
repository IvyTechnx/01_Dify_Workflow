# Banking ワークフロー テスト環境

`industry/banking/test-cases.md` の52テストケースを実行するためのモックAPIサーバーとナレッジベースソースドキュメントです。

## 対象ワークフロー

| ワークフロー | テスト環境の提供物 | テストケース |
|-------------|-------------------|-------------|
| BNK-01 コンプライアンスQ&A | ナレッジベースドキュメント | TC-01〜05 |
| BNK-03 口座サービス案内 | ナレッジベースドキュメント | TC-13, 17 |
| BNK-04 取引モニタリング | モックAPI（取引データ＋エスカレーション） | TC-19〜22 |
| BNK-05 支店実績レポート | モックAPI（支店実績データ） | TC-23〜26 |
| BNK-08 為替レート照会 | モックAPI（為替レートデータ） | TC-36〜40 |

## クイックスタート

### 1. 依存パッケージのインストール

```bash
cd industry/banking/test-env
pip install -r requirements.txt
```

### 2. モックAPIサーバーの起動

```bash
cd mock-server
python app.py
```

サーバーは `http://localhost:5001` で起動します。

### 3. 疎通確認

別のターミナルで：

```bash
python scripts/verify-setup.py
```

全エンドポイントにリクエストを送信し、レスポンスの検証を行います。

## モックAPIエンドポイント

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/health` | GET | ヘルスチェック |
| `/transactions/<id>` | GET | 取引データ取得（BNK-04） |
| `/fraud/escalate` | POST | 不正取引エスカレーション（BNK-04） |
| `/branch-performance?branch=<code>&period=<period>` | GET | 支店実績データ（BNK-05） |
| `/fx-rate?pair=<pair>` | GET | 為替レート（BNK-08） |

### リクエスト例

```bash
# ヘルスチェック
curl http://localhost:5001/health

# 取引データ取得
curl http://localhost:5001/transactions/TXN-20240315-001234

# エスカレーション
curl -X POST http://localhost:5001/fraud/escalate \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"TXN-20240315-001234","risk_level":"HIGH"}'

# 支店実績
curl "http://localhost:5001/branch-performance?branch=BR-001&period=2024Q3"

# 為替レート
curl "http://localhost:5001/fx-rate?pair=USD/JPY"
```

## ナレッジベースの設定

`knowledge-bases/` ディレクトリ内のファイルを Dify のナレッジベースにアップロードしてください。

| ファイル | 対象ワークフロー | 用途 |
|---------|-----------------|------|
| `compliance-kb.md` | BNK-01 | コンプライアンス規程集（反社・AML・個人情報保護等） |
| `account-kb.md` | BNK-03 | 口座サービスご案内（開設・種類・振込・IB等） |

### Dify でのナレッジベース作成手順

1. Dify ダッシュボード → 「ナレッジ」 → 「ナレッジを作成」
2. ファイルをアップロード（ドラッグ＆ドロップ可）
3. インデックス方式: 「高品質」を推奨
4. 作成後、ナレッジベースIDをワークフローの Knowledge Retrieval ノードに設定

## Dify ワークフローへの接続

### HTTP Request ノードの設定

ワークフロー内の HTTP Request ノードの URL を以下に変更してください：

**ローカル環境の場合:**
```
http://localhost:5001/transactions/{{transaction_id}}
http://localhost:5001/branch-performance?branch={{branch_code}}&period={{period}}
http://localhost:5001/fx-rate?pair={{pair}}
http://localhost:5001/fraud/escalate
```

**Dify が Docker で動作している場合:**
```
http://host.docker.internal:5001/transactions/{{transaction_id}}
http://host.docker.internal:5001/branch-performance?branch={{branch_code}}&period={{period}}
http://host.docker.internal:5001/fx-rate?pair={{pair}}
http://host.docker.internal:5001/fraud/escalate
```

## フィクスチャデータ

### transactions.json（4件）

| transaction_id | amount | 期待分岐 | TC |
|---------------|--------|---------|-----|
| TXN-20240315-001234 | 52,000,000 | HIGH → エスカレーション | TC-19 |
| TXN-20240320-005678 | 35,000 | LOW → 通常処理 | TC-20 |
| TXN-20240401-009999 | 15,000,000 | 金額閾値 → エスカレーション | TC-21 |
| TXN/2024+03&15#001 | 500,000 | URL特殊文字テスト | TC-22 |

### branches.json（20件）

BR-001（東京中央）〜 BR-020（鹿児島天文館）の全国20支店分。地域差のある実績データを収録。

### fx-rates.json（4通貨ペア）

| pair | TC | 備考 |
|------|-----|------|
| USD/JPY | TC-36 | 海外送金向け |
| EUR/JPY | TC-37 | 外貨預金向け |
| GBP/JPY | TC-38 | 輸出入決済向け |
| AUD/JPY | TC-39 | 旅行向け |
| THB/JPY | TC-40 | **未対応** → error レスポンス（200） |

## ファイル構成

```
test-env/
├── README.md                        # 本ファイル
├── requirements.txt                 # flask>=2.3.0
├── mock-server/
│   └── app.py                       # Flask モックAPIサーバー
├── fixtures/
│   ├── transactions.json            # BNK-04 用取引データ（4件）
│   ├── branches.json                # BNK-05 用支店データ（20件）
│   └── fx-rates.json                # BNK-08 用為替データ（4通貨ペア）
├── knowledge-bases/
│   ├── compliance-kb.md             # BNK-01 用コンプライアンス規程
│   └── account-kb.md               # BNK-03 用口座サービスご案内
└── scripts/
    └── verify-setup.py              # 疎通確認スクリプト
```
