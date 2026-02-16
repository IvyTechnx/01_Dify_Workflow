# 製造業向け Dify ワークフローサンプル集

製造業の主要業務シーンに対応した 5 つの Dify ワークフロー DSL サンプルです。
すべて `DIFY_WORKFLOW_GOLDEN_RULES.md` に準拠し、Dify へのインポートが可能な形式です。

---

## サンプル一覧

| # | ファイル名 | 業務シーン | パターン | ノード数 |
|---|---|---|---|---|
| 1 | mfg-01-quality-inspection.yml | 品質検査レポート自動生成 | Code(URLエンコード) → API → Code → LLM | 6 |
| 2 | mfg-02-equipment-maintenance.yml | 設備保全アラート対応 | LLM → IF/ELSE → Code(JSON構築) → HTTP | 8 |
| 3 | mfg-03-production-knowledge.yml | 生産現場ナレッジ検索 | RAG (Knowledge → LLM) | 4 |
| 4 | mfg-04-supplier-evaluation.yml | サプライヤー品質評価バッチ | Iteration → LLM 分析 | 7 |
| 5 | mfg-05-work-instruction-translate.yml | 作業手順書多言語翻訳 | Question Classifier 3分岐 | 7 |

**合計ノード数**: 32 ノード

---

## 各ワークフロー詳細

### MFG-01: 品質検査レポート自動生成

**対象部門**: 品質管理部門
**業務シーン**: ロット番号を指定して検査データAPIから品質検査結果を取得し、不良率・良品率を解析、LLMで品質検査レポートを自動生成する。

```
開始 → URLエンコード(Code) → 検査データ取得(HTTP) → データ解析(Code) → レポート生成(LLM) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `lot_number`, `inspection_type` を入力 |
| URLエンコード | code | 入力パラメータを `urllib.parse.quote()` でエンコード |
| 検査データ取得 | http-request | GET `/inspection?lot=...&type=...`（エンコード済み値を使用） |
| データ解析 | code | JSON解析、不良率算出、PASS/FAIL判定 |
| レポート生成 | llm | 品質検査レポートを日本語で生成 (temp: 0.3) |
| 終了 | end | `report` を出力 |

**入力例**:
- `lot_number`: `LOT-2024-A001`
- `inspection_type`: `外観検査`

**カスタマイズポイント**:
- HTTP Request の URL を実際の検査データAPIに変更
- Code ノードの PASS/FAIL 判定閾値（現在: 不良率 5%）を自社基準に調整
- LLM のレポートフォーマットを自社テンプレートに合わせる

---

### MFG-02: 設備保全アラート対応

**対象部門**: 設備保全部門
**業務シーン**: 設備アラートの内容をLLMで分析して緊急度を評価し、重大アラート（critical/emergency）は保全チームにAPI通知、軽微なアラートはセルフサービス保全手順ガイドを生成する。

```
開始 → 緊急度評価(LLM) → 緊急度判定(IF/ELSE)
                              ├─ [LLM出力にcritical / 入力がcritical・emergency] → JSON構築(Code) → 緊急通知送信(HTTP) ─┐
                              └─ [その他]                                        → 保全手順案内(Template)              ─┤
                                                                                                                        → 結果集約(Aggregator) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `equipment_id`, `alert_message`, `alert_level` を入力 |
| 緊急度評価 | llm | アラート内容を分析し緊急度を評価 (temp: 0.2) |
| 緊急度判定 | if-else | LLM出力に "critical" を含む OR `alert_level` が "critical"/"emergency" を含む |
| JSON構築 | code | `json.dumps()` で通知APIのJSONペイロードを安全に構築 |
| 緊急通知送信 | http-request | POST `/maintenance/notify` で保全チームに通知 |
| 保全手順案内 | template-transform | セルフサービス保全手順ガイドを生成 |
| 結果集約 | variable-aggregator | 両分岐の出力を統合 |
| 終了 | end | `response` を出力 |

**入力例**:
- `equipment_id`: `CNC-MILL-003`
- `alert_message`: `主軸モーター温度異常 - 85℃を超過（閾値: 75℃）`
- `alert_level`: `critical`

**カスタマイズポイント**:
- IF/ELSE の条件にアラートレベル文字列を追加（例: "danger", "alarm"）
- HTTP Request の通知先URLを社内通知システム（Slack、Teams等）に変更
- Template Transform の保全手順を自社の標準手順に更新

---

### MFG-03: 生産現場ナレッジ検索

**対象部門**: 生産現場（オペレーター、班長）
**業務シーン**: 作業手順書（SOP）、設備マニュアル、品質基準書をナレッジベースから検索し、LLMが現場の質問に回答する。情報がない場合は担当部署への問い合わせを案内する。

```
開始 → 生産ナレッジ検索(Knowledge Retrieval) → ナレッジ回答生成(LLM, context有効) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `question` を入力 |
| 生産ナレッジ検索 | knowledge-retrieval | ナレッジベースから関連文書を検索 (top_k: 3) |
| ナレッジ回答生成 | llm | 検索結果をコンテキストとして回答 (temp: 0.3) |
| 終了 | end | `answer` を出力 |

**入力例**:
- `question`: `CNC旋盤の工具交換手順を教えてください`

**カスタマイズポイント**:
- `dataset_ids` を実際のナレッジベースIDに変更（Dify上でデータセット作成後）
- `top_k` と `score_threshold` を検索精度に応じて調整
- LLM システムプロンプトの問い合わせ先内線番号を実際の番号に変更
- rerankingモデルを設定して検索精度を向上

---

### MFG-04: サプライヤー品質評価バッチ

**対象部門**: 調達部門、品質管理部門
**業務シーン**: カンマ区切りで指定した複数サプライヤーの品質データ（不良率PPM、納期遵守率、認証情報）をAPIから一括取得し、LLMが総合的な品質評価レポートと推奨順位を生成する。

```
開始 → サプライヤー配列化(Code) → サプライヤーイテレーション ──→ 結果集約(Code) → 品質評価分析(LLM) → 終了
                                      └─ [品質データAPI(HTTP)] ─┘
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `product_code`, `supplier_list` を入力 |
| サプライヤー配列化 | code | カンマ区切り文字列を配列に変換 |
| サプライヤーイテレーション | iteration | 各サプライヤーに対して並列API呼び出し |
| 品質データAPI | http-request | サプライヤー品質データを取得（イテレーション子ノード） |
| 結果集約 | code | APIレスポンスを集約してサマリテキスト生成 |
| 品質評価分析 | llm | 集約データを分析し品質評価レポートを生成 (temp: 0.3) |
| 終了 | end | `evaluation_report` を出力 |

**入力例**:
- `product_code`: `PART-A001`
- `supplier_list`: `SUP-001, SUP-002, SUP-003, SUP-004`

**カスタマイズポイント**:
- HTTP Request のURLを実際のサプライヤー品質管理APIに変更
- 結果集約 Code ノードで取得するメトリクスを追加（例: コスト、リードタイム）
- LLM の評価観点を自社のサプライヤー評価基準に合わせる
- `parallel_mode` を `false` にしてAPI負荷を軽減

---

### MFG-05: 作業手順書翻訳

**対象部門**: 生産技術部門
**業務シーン**: 日本語の作業手順書を指定言語（英語・中国語・ベトナム語）に翻訳する。Question Classifierで言語を判定し、各言語専用のLLM（製造業用語に特化したプロンプト）にルーティングする。

```
開始 → 翻訳言語分類(QC)
           ├─ [英語]       → 英語翻訳(LLM)      ─┐
           ├─ [中国語]     → 中国語翻訳(LLM)     ─┤
           └─ [ベトナム語] → ベトナム語翻訳(LLM)  ─┤
                                                    → 翻訳結果統合(Aggregator) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `instruction_text` (手順書テキスト), `target_language` (言語選択) |
| 翻訳言語分類 | question-classifier | 3クラス: 英語/中国語/ベトナム語 |
| 英語翻訳 | llm | 製造業用語対応の英語翻訳 (temp: 0.2) |
| 中国語翻訳 | llm | 製造業用語対応の中国語翻訳 (temp: 0.2) |
| ベトナム語翻訳 | llm | 製造業用語対応のベトナム語翻訳 (temp: 0.2) |
| 翻訳結果統合 | variable-aggregator | 3分岐の結果を統合 |
| 終了 | end | `translated_instruction` を出力 |

**入力例**:
- `instruction_text`: `1. ワークをバイスに固定する（締付トルク: 25Nm）\n2. 工具をスピンドルに装着する\n3. 加工原点を設定する`
- `target_language`: `English`

**カスタマイズポイント**:
- 対応言語を追加（タイ語、インドネシア語等 → Question Classifier にクラス追加 + LLM追加）
- 各言語LLMのシステムプロンプトに自社固有の専門用語辞書を追加
- `target_language` の選択肢を自社の海外拠点に合わせて変更

---

## インポート手順

1. Dify にログイン
2. 「スタジオ」→「DSLファイルをインポート」
3. 対象の `.yml` ファイルを選択
4. インポート後、以下をカスタマイズ:
   - **モデル設定**: `openai` / `gpt-4o-mini` を利用可能なモデルに変更
   - **API URL**: `api.example.com` を実際のAPIエンドポイントに変更
   - **ナレッジベース**: MFG-03 は `dataset_ids` を実際のデータセットIDに変更

## 使用ノードタイプ一覧

| ノードタイプ | 使用WF |
|---|---|
| start | MFG-01, 02, 03, 04, 05 |
| end | MFG-01, 02, 03, 04, 05 |
| llm | MFG-01, 02, 03, 04, 05 |
| http-request | MFG-01, 02, 04 |
| code | MFG-01, 04 |
| if-else | MFG-02 |
| template-transform | MFG-02 |
| variable-aggregator | MFG-02, 05 |
| knowledge-retrieval | MFG-03 |
| iteration | MFG-04 |
| question-classifier | MFG-05 |

## 前提条件

- Dify v0.6 以上
- OpenAI API キー（または互換モデルプロバイダー）が設定済み
- MFG-03 はナレッジベース（データセット）の事前作成が必要
- MFG-01, 02, 04 は外部API（`api.example.com`）のダミーURL使用。実運用時は実APIに変更
