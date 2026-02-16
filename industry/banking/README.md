# 銀行業向け Dify ワークフローサンプル集

銀行業の主要業務シーンに対応した 10 の Dify ワークフロー DSL サンプルです。
すべて `DIFY_WORKFLOW_GOLDEN_RULES.md` に準拠し、Dify へのインポートが可能な形式です。

---

## サンプル一覧

| # | ファイル名 | 業務シーン | パターン | モード | ノード数 |
|---|---|---|---|---|---|
| 1 | bnk-01-compliance-search.yml | コンプライアンス規程検索 | RAG | workflow | 4 |
| 2 | bnk-02-loan-review.yml | ローン審査書類チェック | PE → Code → IF/ELSE | workflow | 8 |
| 3 | bnk-03-customer-inquiry.yml | 顧客問い合わせ対応 | QC 4分岐 + KR | advanced-chat | 11 |
| 4 | bnk-04-fraud-alert.yml | 不正取引アラート分析 | HTTP → LLM → Code(構造化抽出) → IF/ELSE + JSON安全構築 | workflow | 12 |
| 5 | bnk-05-branch-report.yml | 支店実績レポート一括生成 | Iteration[HTTP] + LLM | workflow | 7 |
| 6 | bnk-06-complaint-classification.yml | 苦情・クレーム自動分類 | QC 5分岐 + LLM×5 | workflow | 9 |
| 7 | bnk-07-ringi-draft.yml | 稟議書ドラフト作成支援 | 多入力 → Code → LLM | workflow | 4 |
| 8 | bnk-08-fx-rate.yml | 外国為替レート照会 | Code(URLenc) → HTTP → Code → LLM | workflow | 6 |
| 9 | bnk-09-sar-draft.yml | 疑わしい取引届出書ドラフト | PE → Code → LLM → Template | workflow | 6 |
| 10 | bnk-10-product-comparison.yml | 金融商品比較レポート | Iteration[LLM] → LLM | workflow | 7 |

**合計ノード数**: 74 ノード

---

## 各ワークフロー詳細

### BNK-01: コンプライアンス規程・法令検索

**対象部門**: コンプライアンス部門、全行員
**業務シーン**: 融資規程、事務取扱要領、AML規程、銀行法、犯罪収益移転防止法等をナレッジベースから検索し、LLMが規程名・条項番号を明示して回答する。

```
開始 → 規程・法令検索(Knowledge Retrieval) → コンプライアンス回答生成(LLM, context有効) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `question` を入力 |
| 規程・法令検索 | knowledge-retrieval | コンプライアンスナレッジベースを検索 (top_k: 5) |
| コンプライアンス回答生成 | llm | 検索結果をコンテキストとして回答 (temp: 0.2) |
| 終了 | end | `answer` を出力 |

**入力例**:
- `question`: `反社会的勢力との取引に関する社内規程を教えてください`

**カスタマイズポイント**:
- `dataset_ids` を実際のコンプライアンスナレッジベースIDに変更
- 問い合わせ先内線番号（現在: 5001）を実際の番号に変更
- rerankingモデルを設定して検索精度を向上

---

### BNK-02: ローン審査 基本要件チェック

**対象部門**: 融資審査部門
**業務シーン**: ローン申請書テキストからParameter Extractorで申請者情報を抽出し、Codeで基本要件（年齢20〜70歳、年収200万円以上、勤続1年以上、借入比率8倍以下）をチェック。合格ならLLMで審査レポート、不合格ならテンプレートで不適合通知を生成。

```
開始 → 申請情報抽出(PE) → 基本要件チェック(Code) → 要件判定分岐(IF/ELSE)
                                                        ├─ [PASS] → 審査レポート生成(LLM)     ─┐
                                                        └─ [FAIL] → 不適合通知生成(Template)   ─┤
                                                                                                  → 結果集約(Aggregator) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `application_text` を入力 |
| 申請情報抽出 | parameter-extractor | 氏名、年齢、年収、勤続年数、借入希望額、借入目的を抽出 |
| 基本要件チェック | code | 年齢・年収・勤続・借入比率の4項目を判定 |
| 要件判定分岐 | if-else | Code出力の `result` が "PASS" か判定 |
| 審査レポート生成 | llm | 合格者向けの詳細審査レポートを生成 (temp: 0.3) |
| 不適合通知生成 | template-transform | 不合格項目を明示した不適合通知を生成 |
| 結果集約 | variable-aggregator | 両分岐の出力を統合 |
| 終了 | end | `review_result` を出力 |

**入力例**:
- `application_text`: `申請者: 田中太郎、年齢35歳、年収650万円、勤続8年、借入希望額3000万円、目的: 住宅ローン`

**カスタマイズポイント**:
- Code ノードの審査基準値（年齢範囲、最低年収、勤続年数、借入比率上限）を自行の審査基準に変更
- Parameter Extractor の抽出パラメータを追加（例: 勤務先、既存借入額）
- LLM の審査レポートフォーマットを自行テンプレートに合わせる

---

### BNK-03: 顧客問い合わせ対応チャット

**対象部門**: コールセンター、窓口
**業務シーン**: 顧客問い合わせを「口座」「ローン」「カード」「その他」に4分類し、口座系はナレッジ検索+LLM、それ以外は専用LLMで回答。Chatflow形式で会話履歴を保持。

```
開始 → 問い合わせ分類(QC)
           ├─ [口座] → 口座ナレッジ検索(KR) → 口座対応LLM → 口座回答(Answer)
           ├─ [ローン]                      → ローン対応LLM → ローン回答(Answer)
           ├─ [カード]                      → カード対応LLM → カード回答(Answer)
           └─ [その他]                      → 一般対応LLM   → 一般回答(Answer)
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `sys.query` を使用（Chatflow） |
| 問い合わせ分類 | question-classifier | 4クラス: 口座/ローン/カード/その他 |
| 口座ナレッジ検索 | knowledge-retrieval | 口座関連ナレッジベースを検索 |
| 口座対応LLM | llm | context有効 + memory有効 (temp: 0.3) |
| ローン対応LLM | llm | memory有効 (temp: 0.3) |
| カード対応LLM | llm | memory有効 (temp: 0.3) |
| 一般対応LLM | llm | memory有効 (temp: 0.3) |
| 口座/ローン/カード/一般回答 | answer ×4 | 各分岐の回答を出力 |

**入力例**:
- `普通預金口座の開設に必要な書類を教えてください`
- `住宅ローンの金利を教えてください`
- `クレジットカードのポイント還元率は？`

**カスタマイズポイント**:
- `dataset_ids` を実際の口座関連ナレッジベースIDに変更
- Question Classifier の分類ルールに自行固有のサービス名を追加
- 各LLMのシステムプロンプトに自行の商品情報・規約を反映
- `memory.window.size` を調整（現在: 10ターン）

---

### BNK-04: 不正取引アラート分析・エスカレーション

**対象部門**: 不正検知部門、コンプライアンス部門
**業務シーン**: トランザクションIDを指定してAPIから取引データを取得、LLMで不正パターン（HIGH/MEDIUM/LOW）を分析。HIGHリスクまたは1000万円超の取引はJSON安全構築の上で通知APIにエスカレーション。

```
開始 → URLエンコード(Code) → 取引データ取得(HTTP) → データ整形(Code) → 不正分析(LLM) → リスク判定抽出(Code) → エスカレーション判定(IF/ELSE)
                                                                                                                       ├─ [HIGH or 1000万超] → JSON構築(Code) → エスカレーション通知(HTTP) ─┐
                                                                                                                       └─ [それ以外]         → 通常処理(Template)                        ─┤
                                                                                                                                                                                           → 結果集約(Aggregator) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `transaction_id`, `alert_type` を入力 |
| URLエンコード | code | `urllib.parse.quote()` で取引IDをエンコード |
| 取引データ取得 | http-request | GET `/transactions/{id}` で取引データ取得 |
| データ整形 | code | JSON解析、金額を `float()` 変換、取引サマリ生成 |
| 不正分析 | llm | 不正パターン分析、HIGH/MEDIUM/LOW判定 (temp: 0.2) |
| リスク判定抽出 | code | 正規表現で `リスク評価: HIGH/MEDIUM/LOW` を構造化抽出 |
| エスカレーション判定 | if-else | `risk_level` が "HIGH" (厳密一致) OR 金額 > 1000万円 |
| JSON構築 | code | `json.dumps()` で通知ペイロードを安全構築 |
| エスカレーション通知 | http-request | POST `/fraud/escalate` で通知送信 |
| 通常処理 | template-transform | モニタリング記録レポートを生成 |
| 結果集約 | variable-aggregator | 両分岐の出力を統合 |
| 終了 | end | `analysis_result` を出力 |

**入力例**:
- `transaction_id`: `TXN-20240315-001234`
- `alert_type`: `高額海外送金`

**カスタマイズポイント**:
- HTTP Request のURLを実際のトランザクション管理APIに変更
- IF/ELSE の金額閾値（現在: 1000万円）を自行基準に変更
- LLM の不正判定基準を自行のAMLポリシーに合わせる
- エスカレーション通知先を社内通知システム（Slack、Teams等）に変更

---

### BNK-05: 支店実績経営分析レポート

**対象部門**: 経営企画部門
**業務シーン**: カンマ区切りで指定した複数支店の実績データ（預金残高、貸出残高、利益、新規口座数）をAPIから一括取得し、LLMが全体分析・優良支店/要改善支店の評価・経営提言を含むレポートを生成。

```
開始 → 支店配列化(Code) → 支店イテレーション ──→ 結果集約(Code) → 経営分析(LLM) → 終了
                             └─ [実績API(HTTP)] ─┘
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `branch_list`, `report_period` を入力 |
| 支店配列化 | code | カンマ区切り → 配列変換 + レポート期間URLエンコード |
| 支店イテレーション | iteration | 各支店に対して並列API呼び出し |
| 実績API | http-request | 支店実績データを取得（イテレーション子ノード） |
| 結果集約 | code | APIレスポンスを集約してサマリテキスト生成 |
| 経営分析 | llm | 全支店データを分析し経営レポートを生成 (temp: 0.3) |
| 終了 | end | `report` を出力 |

**入力例**:
- `branch_list`: `BR-001, BR-002, BR-003, BR-004, BR-005`
- `report_period`: `2024Q3`

**カスタマイズポイント**:
- HTTP Request のURLを実際の支店実績管理APIに変更
- 結果集約 Code ノードで取得するメトリクスを追加（例: 顧客満足度、従業員数）
- LLM のレポートフォーマットを経営会議用テンプレートに合わせる
- `parallel_mode` を `false` にしてAPI負荷を軽減

---

### BNK-06: 苦情・クレーム自動分類・対応案生成

**対象部門**: 顧客相談室、コンプライアンス部門
**業務シーン**: 顧客からの苦情テキストを「サービス品質」「手数料・費用」「システム障害」「従業員対応」「その他」の5カテゴリに自動分類し、カテゴリ別に専門的な対応案（感情分析・要約・推奨対応・エスカレーション要否）を生成する。

```
開始 → 苦情分類(QC 5分岐)
           ├─ [サービス品質] → サービス品質対応(LLM) ─┐
           ├─ [手数料]       → 手数料対応(LLM)       ─┤
           ├─ [システム障害] → システム障害対応(LLM)   ─┤→ 結果集約(Aggregator) → 終了
           ├─ [従業員対応]   → 従業員対応(LLM)       ─┤
           └─ [その他]       → その他対応(LLM)       ─┘
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `complaint_text`, `customer_segment`(select) を入力 |
| 苦情分類 | question-classifier | 5クラス: サービス品質/手数料/システム障害/従業員対応/その他 |
| サービス品質対応 | llm | SLA基準との乖離分析 (temp: 0.3) |
| 手数料対応 | llm | 手数料規程確認・見直し検討 (temp: 0.3) |
| システム障害対応 | llm | 障害状況確認・代替手段案内 (temp: 0.3) |
| 従業員対応 | llm | 事実確認プロセス・再発防止策 (temp: 0.3) |
| その他対応 | llm | 適切な担当部署への転送案内 (temp: 0.3) |
| 結果集約 | variable-aggregator | 5つのLLM出力を集約 |
| 終了 | end | `response` を出力 |

**入力例**:
- `complaint_text`: `先週ATMで振込をしようとしたところ、3回もエラーが出て結局窓口に行く羽目になりました。30分も無駄にしました。`
- `customer_segment`: `個人`

**カスタマイズポイント**:
- Question Classifier の分類カテゴリを自行の苦情分類体系に変更
- 各LLMの対応ルールに自行のクレーム対応マニュアルを反映
- `customer_segment` の選択肢を自行の顧客セグメントに変更

---

### BNK-07: 稟議書ドラフト作成支援

**対象部門**: 融資審査部門、営業推進部門
**業務シーン**: 融資案件の基本情報（企業名、業種、金額、期間、金利、担保、目的、財務概要）を入力し、Codeで整形した上でLLMが社内稟議書フォーマットのドラフトを生成。件名、申請概要、財務分析、案件評価、審査意見を含む。

```
開始(8入力) → 入力整形(Code) → 稟議書生成(LLM, max_tokens: 8192) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | 8パラメータ: company_name, industry, loan_amount, loan_term, interest_rate, collateral, purpose, financial_summary |
| 入力整形 | code | 入力パラメータを稟議書用に整形 |
| 稟議書生成 | llm | 融資稟議書フォーマットでドラフト生成 (temp: 0.3, max_tokens: 8192) |
| 終了 | end | `ringi_draft` を出力 |

**入力例**:
- `company_name`: `株式会社サンプル製造`
- `industry`: `製造業（精密機器）`
- `loan_amount`: `5000`（万円）
- `loan_term`: `5年`
- `interest_rate`: `1.2%`
- `collateral`: `本社工場建物（評価額3億円）、代表者連帯保証`
- `purpose`: `新工場建設資金`
- `financial_summary`: `売上高15億円、経常利益8000万円、自己資本比率35%`

**カスタマイズポイント**:
- LLM の稟議書フォーマットを自行の稟議書テンプレートに変更
- 入力パラメータを追加（例: 既存取引実績、信用格付け）
- `max_tokens` を稟議書の想定文量に応じて調整

---

### BNK-08: 外国為替レート照会・顧客向け解説

**対象部門**: 外国為替窓口、営業部門
**業務シーン**: 通貨ペアを指定して為替レートAPIから最新レートを取得、Codeでパース後、顧客の利用目的（海外送金/外貨預金/輸出入決済/旅行）に応じたわかりやすい解説をLLMが生成する。

```
開始 → URLエンコード(Code) → 為替レート取得(HTTP) → レート解析(Code) → 顧客向け解説(LLM) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `currency_pair`, `customer_purpose`(select) を入力 |
| URLエンコード | code | `urllib.parse.quote()` で通貨ペアをエンコード |
| 為替レート取得 | http-request | GET `/fx-rate?pair={pair}` でレート取得 |
| レート解析 | code | JSON解析、Bid/Ask/仲値/スプレッド/24H変動率を整形 |
| 顧客向け解説 | llm | 利用目的に応じた解説生成 (temp: 0.5) |
| 終了 | end | `rate_explanation` を出力 |

**入力例**:
- `currency_pair`: `USD/JPY`
- `customer_purpose`: `海外送金`

**カスタマイズポイント**:
- HTTP Request のURLを実際の為替レートAPIに変更
- レート解析 Code ノードのフィールド名をAPIレスポンスに合わせる
- LLM の注意事項に自行の為替手数料体系を反映
- `customer_purpose` の選択肢を追加（例: 外貨建て投信）

---

### BNK-09: 疑わしい取引の届出書ドラフト作成

**対象部門**: AML/CFT担当部門
**業務シーン**: 疑わしい取引の詳細テキストからParameter Extractorで顧客情報・取引情報を抽出し、Codeで検証・整形、LLMが犯罪収益移転防止法に基づく分析を行い、Templateで届出書フォーマットに整形する。

```
開始 → パラメータ抽出(PE) → 検証・整形(Code) → 疑義分析・ドラフト(LLM) → 届出書フォーマット(Template) → 終了
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `transaction_details` を入力 |
| パラメータ抽出 | parameter-extractor | 顧客名、種別、口座番号、金額、日付、種別、理由を抽出 |
| 検証・整形 | code | 抽出パラメータの欠損チェック + 整形 |
| 疑義分析・ドラフト | llm | 犯収法観点での分析と届出内容ドラフト生成 (temp: 0.2) |
| 届出書フォーマット | template-transform | 公式フォーマットに整形 |
| 終了 | end | `sar_draft` を出力 |

**入力例**:
- `transaction_details`: `顧客: 山田商事（法人）、口座: 1234567、2024年3月15日に海外送金5000万円を実行。過去3ヶ月の取引履歴と比較して著しく高額。送金先はケイマン諸島の法人口座。合理的な事業目的の説明なし。`

**カスタマイズポイント**:
- Parameter Extractor の抽出項目を自行のSARフォーマットに合わせて追加
- LLM の分析基準を最新の犯収法ガイドラインに更新
- Template の届出書フォーマットを自行の提出様式に変更

---

### BNK-10: 金融商品比較レポート生成

**対象部門**: 商品企画部門、営業推進部門
**業務シーン**: 比較したい金融商品名を改行区切りで入力し、Iteration内のLLMが各商品を個別分析（カテゴリ、リスク、リターン、手数料、ターゲット顧客）、その後LLMが比較観点に基づく総括レポートを生成する。

```
開始 → 商品配列化(Code) → 商品分析イテレーション ──→ 結果集約(Code) → 比較総括(LLM) → 終了
                             └─ [商品個別分析(LLM)] ─┘
```

| ノード | タイプ | 説明 |
|---|---|---|
| 開始 | start | `product_list`(改行区切り), `comparison_focus`(select) を入力 |
| 商品配列化 | code | 改行区切り → 配列変換 |
| 商品分析イテレーション | iteration | 各商品を並列でLLM分析 |
| 商品個別分析 | llm | カテゴリ/リスク/リターン/手数料/ターゲットを分析 (temp: 0.3) |
| 結果集約 | code | 個別分析結果を集約テキスト化 |
| 比較総括 | llm | 比較観点に基づく総括レポート生成 (temp: 0.3, max_tokens: 8192) |
| 終了 | end | `comparison_report` を出力 |

**入力例**:
- `product_list`:
  ```
  定期預金（1年）
  個人向け国債（変動10年）
  バランス型投資信託
  外貨建て定期預金（米ドル）
  ```
- `comparison_focus`: `リスク・リターン`

**カスタマイズポイント**:
- 個別分析 LLM のプロンプトに自行取扱商品の詳細情報を追加
- `comparison_focus` の選択肢を営業シーンに合わせて変更
- `parallel_mode` を `false` にしてAPI負荷を軽減

---

## インポート手順

1. Dify にログイン
2. 「スタジオ」→「DSLファイルをインポート」
3. 対象の `.yml` ファイルを選択
4. インポート後、以下をカスタマイズ:
   - **モデル設定**: `openai` / `gpt-4o-mini` を利用可能なモデルに変更
   - **API URL**: `api.example.com` を実際のAPIエンドポイントに変更（BNK-04, 05, 08）
   - **ナレッジベース**: BNK-01, BNK-03 は `dataset_ids` を実際のデータセットIDに変更

## 使用ノードタイプ一覧

| ノードタイプ | 使用WF |
|---|---|
| start | BNK-01〜10（全WF） |
| end | BNK-01, 02, 04〜10 |
| answer | BNK-03 |
| llm | BNK-01〜10（全WF） |
| knowledge-retrieval | BNK-01, 03 |
| question-classifier | BNK-03, 06 |
| parameter-extractor | BNK-02, 09 |
| if-else | BNK-02, 04 |
| code | BNK-02, 04, 05, 07, 08, 09, 10 |
| http-request | BNK-04, 05, 08 |
| template-transform | BNK-02, 04, 09 |
| variable-aggregator | BNK-02, 04, 06 |
| iteration | BNK-05, 10 |

## 設計上の考慮事項（銀行業固有）

- **個人情報保護**: 全LLMシステムプロンプトに個人情報の生成・推測禁止を明記
- **コンプライアンス**: 法令解釈は参考情報であり、最終判断は専門部署確認を促す
- **安全側判定**: 不正検知・審査において疑わしい場合は安全側（厳格側）に判定
- **エスカレーション**: 自動判定で処理完結せず、必要に応じて人間の専門家に引き継ぐ設計
- **監査証跡**: End/Answer ノードで全結果を出力し、後続の記録・監査に対応
- **適合性原則**: 金融商品の推奨において顧客属性・リスク許容度を考慮（BNK-10）
- **AML/CFT**: 疑わしい取引は事実と推測を区別し、断定的な犯罪性表現を回避（BNK-04, 09）

## 前提条件

- Dify v0.6 以上
- OpenAI API キー（または互換モデルプロバイダー）が設定済み
- BNK-01, BNK-03 はナレッジベース（データセット）の事前作成が必要
- BNK-04, BNK-05, BNK-08 は外部API（`api.example.com`）のダミーURL使用。実運用時は実APIに変更
