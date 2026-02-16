# 小売・EC業向け Dify ワークフローサンプル集

小売・EC業の主要業務シーンに対応した **10** の Dify ワークフロー DSL サンプルです。
すべて `DIFY_WORKFLOW_GOLDEN_RULES.md` に準拠し、Dify へのインポートが可能な形式です。

---

## サンプル一覧

| # | ファイル名 | 業務シーン | パターン | モード | ノード数 |
|---|---|---|---|---|---|
| 1 | rtl-01-product-description.yml | 商品説明文自動生成 | Code→LLM→TT | workflow | 5 |
| 2 | rtl-02-review-analysis.yml | カスタマーレビュー分析 | PE→Code→LLM→TT | workflow | 6 |
| 3 | rtl-03-product-inquiry-chat.yml | 商品問い合わせチャット | QC(3分岐)→KR×2→LLM×3→Answer×3 | **chatflow** | 10 |
| 4 | rtl-04-inventory-alert.yml | 在庫アラート＆発注提案 | HTTP→Code→IF/ELSE→LLM/TT→VA | workflow | 8 |
| 5 | rtl-05-recommend-email.yml | 商品レコメンドメール | Code→QC(3分岐)→LLM×3→VA | workflow | 8 |
| 6 | rtl-06-return-complaint.yml | 返品・クレーム対応 | PE→Code→IF/ELSE→LLM/TT→VA | workflow | 8 |
| 7 | rtl-07-competitor-pricing.yml | 競合価格モニタリング | Code→Iteration[HTTP]→Code→LLM | workflow | 7 |
| 8 | rtl-08-product-categorizer.yml | 商品カテゴリ自動分類 | Code→QC(4分岐)→LLM×4→VA | workflow | 9 |
| 9 | rtl-09-campaign-planner.yml | キャンペーン企画書 | Code→LLM(8192tok)→TT | workflow | 5 |
| 10 | rtl-10-multi-store-daily-report.yml | 多店舗売上日報 | Code→Iteration[HTTP]→Code→LLM | workflow | 7 |

**合計ノード数**: 73 ノード

---

## 各ワークフロー詳細

### RTL-01: 商品説明文自動生成

**対象部門**: EC運営 / 商品企画
**業務シーン**: 新商品登録時に、商品情報からSEO対応の説明文を自動生成

```
開始 → 入力整形(Code) → 説明文生成(LLM) → 出力フォーマット(TT) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | product_name, category(7択), features, target_audience, price_range |
| 入力整形 | code | 入力を構造化テキストに変換、詳細レベル判定 |
| 説明文生成 | llm | キャッチコピー＋概要＋特徴＋おすすめ対象を生成 |
| 出力フォーマット | template-transform | ヘッダー＋メタ情報＋本文のレポート形式に整形 |
| 終了 | end | product_description |

**カスタマイズポイント**:
- `category` の選択肢を自社の商品カテゴリに合わせる
- LLMプロンプトの出力構成（SEOキーワード戦略等）を調整

---

### RTL-02: カスタマーレビュー分析・要約

**対象部門**: CS / マーケティング / 商品開発
**業務シーン**: レビューを構造化分析し、商品改善や販促に活用

```
開始 → レビュー情報抽出(PE) → 感情スコアリング(Code) → 分析要約生成(LLM) → レポート整形(TT) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | review_text, product_name |
| レビュー情報抽出 | parameter-extractor | 感情、推定評価、良い点、悪い点、トピック |
| 感情スコアリング | code | 感情＋評価値から0-100スコア算出、GOOD/NEUTRAL/POOR判定 |
| 分析要約生成 | llm | 評価ポイント＋改善ポイント＋販促提案 |
| レポート整形 | template-transform | メトリクス＋分析コメントのレポート形式 |
| 終了 | end | review_report |

**カスタマイズポイント**:
- 感情スコアの基準値（GOOD≥70, NEUTRAL≥40）を自社基準に調整
- 複数レビューの一括分析はIterationとの組み合わせで拡張可能

---

### RTL-03: 商品問い合わせチャットボット

**対象部門**: CS（カスタマーサポート）
**業務シーン**: 顧客からの問い合わせを自動分類し、ナレッジベースを活用して回答

```
開始 → 問い合わせ分類(QC) ─┬─ 商品情報検索(KR) → 商品回答(LLM) → 応答出力(Answer)
                            ├─ 注文配送検索(KR) → 注文回答(LLM) → 応答出力(Answer)
                            └─ 返品交換回答(LLM) → 応答出力(Answer)
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | Chatflow（sys.query） |
| 問い合わせ分類 | question-classifier | 商品情報 / 注文・配送 / 返品・交換 の3分岐 |
| 商品情報検索 | knowledge-retrieval | 商品カタログKBを検索 |
| 商品回答 | llm | 商品情報に基づく回答（memory有効） |
| 注文配送検索 | knowledge-retrieval | 注文・配送ポリシーKBを検索 |
| 注文配送回答 | llm | 注文配送に関する回答（memory有効） |
| 返品交換回答 | llm | 返品ポリシーに基づく回答（memory有効） |
| Answer×3 | answer | 各分岐の応答出力 |

**カスタマイズポイント**:
- `dataset_ids` を実際のナレッジベースIDに変更
- 返品ポリシー（日数、条件等）をLLMプロンプト内で自社規定に合わせる
- 会話変数 `inquiry_category` を活用してエスカレーション判定を追加可能

---

### RTL-04: 在庫アラート＆発注提案

**対象部門**: 在庫管理 / 購買
**業務シーン**: 在庫APIから取得した在庫数を閾値と比較し、発注提案または正常レポートを出力

```
開始 → 在庫API取得(HTTP) → 閾値判定(Code) → アラート判定(IF/ELSE)
                                                 ├─ [ALERT] 発注提案生成(LLM)
                                                 └─ [OK] 在庫正常レポート(TT)
                                              → 結果集約(VA) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | product_id, warehouse_id(4倉庫) |
| 在庫API取得 | http-request | 在庫管理APIからデータ取得 |
| 閾値判定 | code | 発注点・安全在庫・在庫切れ日数を算出 |
| アラート判定 | if-else | ALERT/OK で分岐 |
| 発注提案生成 | llm | 推奨発注数・緊急度・リスク評価を含む提案 |
| 在庫正常レポート | template-transform | 正常ステータスの定型レポート |
| 結果集約 | variable-aggregator | 分岐出力を統合 |
| 終了 | end | inventory_report |

**カスタマイズポイント**:
- APIエンドポイントを実際の在庫管理システムに変更
- 倉庫の選択肢を自社拠点に合わせる
- 閾値（reorder_point, safety_stock計算式）を自社基準に調整

---

### RTL-05: 商品レコメンドメール生成

**対象部門**: CRM / マーケティング
**業務シーン**: 顧客セグメント別に最適化されたレコメンドメールを自動生成

```
開始 → 履歴分析(Code) → セグメント振分(QC) ─┬─ VIPメール生成(LLM)
                                               ├─ リピーターメール生成(LLM)
                                               └─ 新規メール生成(LLM)
                                            → メール集約(VA) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | customer_segment(3択), purchase_history, campaign_type(4択) |
| 履歴分析 | code | 購買回数算出、プロファイルテキスト生成 |
| セグメント振分 | question-classifier | VIP / リピーター / 新規 の3分岐 |
| VIPメール | llm | 限定感・特別感のある文面 |
| リピーターメール | llm | 感謝＋関連商品の親しみやすい文面 |
| 新規メール | llm | ウェルカム＋人気商品の安心感ある文面 |
| メール集約 | variable-aggregator | 各セグメントの出力を統合 |
| 終了 | end | recommend_email |

**カスタマイズポイント**:
- セグメント基準を自社CRM定義に合わせる
- 各セグメントのオファー内容（クーポン率、特典等）をプロンプトで調整
- campaign_type の選択肢を追加可能

---

### RTL-06: 返品・クレーム対応ドラフト

**対象部門**: CS（カスタマーサポート）
**業務シーン**: クレーム内容を構造化分析し、重要度に応じた対応ドラフトまたはエスカレーション通知を生成

```
開始 → クレーム情報抽出(PE) → 重要度判定(Code) → エスカレ判定(IF/ELSE)
                                                    ├─ [NORMAL] 対応ドラフト生成(LLM)
                                                    └─ [ESCALATE] エスカレーション通知(TT)
                                                 → 結果集約(VA) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | complaint_text, order_number |
| クレーム情報抽出 | parameter-extractor | 問題種別、商品名、感情レベル、希望対応、購入日 |
| 重要度判定 | code | 問題種別＋感情＋希望対応から0-8スコア算出 |
| エスカレ判定 | if-else | NORMAL(5未満) / ESCALATE(5以上) で分岐 |
| 対応ドラフト | llm | お詫び→状況確認→対応案→改善の構成でメール生成 |
| エスカレ通知 | template-transform | 上席引き継ぎ用の構造化通知 |
| 結果集約 | variable-aggregator | 分岐出力を統合 |
| 終了 | end | complaint_response |

**カスタマイズポイント**:
- エスカレーション閾値（デフォルト: 5/8）を自社基準に調整
- 問題種別・感情レベルのスコア配分を変更可能
- LLMプロンプトの返品ポリシーを自社規定に合わせる

---

### RTL-07: 競合価格モニタリングレポート

**対象部門**: MD（マーチャンダイジング）/ 経営企画
**業務シーン**: 複数競合の価格データをAPI一括取得し、価格戦略レポートを生成

```
開始 → 競合配列化(Code) → 競合イテレーション[価格API(HTTP)] → 価格データ集約(Code) → 価格分析(LLM) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | competitor_list(カンマ区切り), product_category |
| 競合配列化 | code | 競合名を配列化＋URLエンコード |
| 競合イテレーション | iteration | 並列実行、エラー時続行 |
| 価格API | http-request | 各競合の価格データ取得 |
| 価格データ集約 | code | JSONパース＋比較テキスト生成 |
| 価格分析 | llm | 価格ポジション分析＋戦略提言 |
| 終了 | end | pricing_report |

**カスタマイズポイント**:
- APIエンドポイントを実際の価格監視サービスに変更
- 分析レポートの出力項目をカスタマイズ

---

### RTL-08: 商品カテゴリ自動分類

**対象部門**: EC運営 / 商品マスタ管理
**業務シーン**: 新商品情報テキストを4大カテゴリに自動分類し、カテゴリ固有のタグ・属性情報を生成

```
開始 → 入力検証(Code) → カテゴリ分類(QC) ─┬─ 食品タグ生成(LLM)
                                             ├─ アパレルタグ生成(LLM)
                                             ├─ 家電タグ生成(LLM)
                                             └─ 日用品タグ生成(LLM)
                                          → 分類結果集約(VA) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | product_info |
| 入力検証 | code | テキスト長チェック、警告付加 |
| カテゴリ分類 | question-classifier | 食品/アパレル/家電/日用品の4分岐 |
| 食品タグ | llm | アレルギー表示、保存方法、賞味期限等 |
| アパレルタグ | llm | サイズ展開、素材、シーズン等 |
| 家電タグ | llm | スペック、対応規格、保証期間等 |
| 日用品タグ | llm | 素材、サイズ、使用シーン等 |
| 分類結果集約 | variable-aggregator | 各カテゴリの出力を統合 |
| 終了 | end | categorization_result |

**カスタマイズポイント**:
- 4カテゴリを自社の商品分類体系に合わせて変更
- 各カテゴリのタグ項目をバックエンドの商品マスタスキーマに合わせる
- 分類精度向上のためQCの instruction を調整

---

### RTL-09: キャンペーン企画書ドラフト

**対象部門**: マーケティング / 販促企画
**業務シーン**: 6つの入力からキャンペーン企画書のフルドラフトを自動生成

```
開始 → 入力整形(Code) → 企画書生成(LLM) → 企画書フォーマット(TT) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | campaign_name, target_segment(5択), budget, duration, objectives, channels(6択) |
| 入力整形 | code | 6入力を構造化ブリーフに変換 |
| 企画書生成 | llm | 8セクション構成の本格企画書（max_tokens: 8192） |
| 企画書フォーマット | template-transform | ヘッダー＋メタ情報表＋本文＋注記 |
| 終了 | end | campaign_plan |

**カスタマイズポイント**:
- `target_segment`, `channels` の選択肢を自社のセグメント定義に合わせる
- 企画書のセクション構成を社内テンプレートに合わせて調整
- 予算配分のロジックを自社の標準比率に変更

---

### RTL-10: 多店舗売上日報一括生成

**対象部門**: 店舗運営 / エリアマネージャー
**業務シーン**: 複数店舗の売上データをAPI一括取得し、全店横断の日次売上レポートを生成

```
開始 → 店舗配列化(Code) → 店舗イテレーション[売上API(HTTP)] → 売上データ集約(Code) → 日報生成(LLM) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | store_list(カンマ区切り), report_date |
| 店舗配列化 | code | 店舗名を配列化＋URLエンコード |
| 店舗イテレーション | iteration | 並列実行、エラー時続行 |
| 売上API | http-request | 各店舗の売上データ取得 |
| 売上データ集約 | code | JSONパース＋全店合計算出 |
| 日報生成 | llm | 店舗別実績＋トレンド分析＋翌日アクション |
| 終了 | end | daily_report |

**カスタマイズポイント**:
- APIエンドポイントを実際のPOSシステム/BIツールに変更
- KPI項目（客単価、坪効率等）を追加可能
- レポートフォーマットを社内テンプレートに合わせる

---

## インポート手順

1. Dify にログイン
2. 「スタジオ」→「DSLファイルをインポート」
3. 対象の `.yml` ファイルを選択
4. インポート後、以下をカスタマイズ:
   - **モデル設定**: `openai` / `gpt-4o-mini` を利用可能なモデルに変更
   - **API URL**: `api.example.com` を実際のAPIエンドポイントに変更
   - **ナレッジベース**: `dataset_ids` を実際のデータセットIDに変更（RTL-03）

---

## 使用ノードタイプ一覧

| ノードタイプ | 使用WF |
|---|---|
| start | RTL-01〜10（全WF） |
| end | RTL-01,02,04〜10 |
| answer | RTL-03 |
| llm | RTL-01〜10（全WF） |
| code | RTL-01,02,04,05,07,08,09,10 |
| parameter-extractor | RTL-02, 06 |
| question-classifier | RTL-03, 05, 08 |
| knowledge-retrieval | RTL-03 |
| http-request | RTL-04, 07, 10 |
| iteration | RTL-07, 10 |
| if-else | RTL-04, 06 |
| template-transform | RTL-01, 04, 06, 09 |
| variable-aggregator | RTL-04, 05, 06, 08 |

---

## 設計上の考慮事項（小売・EC業固有）

- **個人情報保護**: 顧客の住所・電話番号等をLLMプロンプトに含めない設計
- **景品表示法対応**: 商品説明文・キャンペーン企画に誇大表現防止ルールを組み込み
- **特定商取引法**: メール生成に配信停止リンク案内を必須化
- **返品ポリシー**: 法定期間（クーリングオフ等）との整合性を考慮
- **価格戦略**: 独占禁止法に抵触するカルテル的提案の禁止をLLMプロンプトに明記
- **在庫管理**: APIデータはリアルタイムではなく参考値である旨を付記

## 前提条件

- Dify v0.6 以上
- OpenAI API キー（または互換モデルプロバイダー）が設定済み
- RTL-03: 商品カタログ／注文ポリシーのナレッジベースが作成済み
- RTL-04, 07, 10: 対応するAPIエンドポイントが利用可能
