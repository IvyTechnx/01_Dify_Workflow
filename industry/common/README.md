# 共通業務系 Dify ワークフロー (CMN-01〜10)

業種を問わず、あらゆる企業で活用できる**共通業務ワークフロー**のサンプル DSL 集です。
日本企業の典型的な間接業務（日報・議事録・稟議・経費精算・ヘルプデスク等）を Dify で自動化するリファレンスとして設計されています。

## ワークフロー一覧

| # | ID | ワークフロー名 | ノード数 | モード | 対象部門 |
|---|-----|---------------|---------|--------|---------|
| 1 | CMN-01 | [社内規程・就業規則Q&A](#cmn-01-社内規程就業規則qa) | 4 | workflow | 総務部 / 全社員 |
| 2 | CMN-02 | [日報自動生成](#cmn-02-日報自動生成) | 5 | workflow | 全部門 |
| 3 | CMN-03 | [議事録要約・アクションアイテム抽出](#cmn-03-議事録要約アクションアイテム抽出) | 7 | workflow | 全部門 |
| 4 | CMN-04 | [経費申請チェック](#cmn-04-経費申請チェック) | 8 | workflow | 経理部 / 全社員 |
| 5 | CMN-05 | [社内ヘルプデスクチャット](#cmn-05-社内ヘルプデスクチャット) | 10 | **chatflow** | 情シス / 全社員 |
| 6 | CMN-06 | [契約書リスクレビュー](#cmn-06-契約書リスクレビュー) | 9 | workflow | 法務部 / 営業部 |
| 7 | CMN-07 | [稟議書ドラフト作成（汎用版）](#cmn-07-稟議書ドラフト作成汎用版) | 5 | workflow | 全部門 / 管理職 |
| 8 | CMN-08 | [採用候補者スクリーニング](#cmn-08-採用候補者スクリーニング) | 8 | workflow | 人事部 |
| 9 | CMN-09 | [部門別KPIレポート一括生成](#cmn-09-部門別kpiレポート一括生成) | 7 | workflow | 経営企画部 |
| 10 | CMN-10 | [営業メール自動生成](#cmn-10-営業メール自動生成) | 12 | workflow | 営業部 |

**合計: 10 ワークフロー / 75 ノード**

---

## 設計方針

| 方針 | 説明 |
|------|------|
| **業種非依存** | 製造業・金融・サービス業など業種を問わず利用可能な汎用業務をカバー |
| **日本企業文化対応** | 稟議書、日報、議事録、敬語メールなど日本特有のビジネス慣習に対応 |
| **ノードパターン網羅** | Dify の全主要ノードタイプ（LLM, Code, KR, QC, PE, IF/ELSE, Iteration, TT, VA）を活用 |
| **安全設計** | 全ワークフローで `sensitive_word_avoidance` 有効化、個人情報保護ルール組込み |
| **3層ガード** | CMN-06 で入力検証→KR連携LLM→出力検証の Guarded Pipeline パターンを実装 |
| **段階的難易度** | 4ノード（RAG基本）から12ノード（複合型）まで段階的に複雑化 |

---

## ノードパターン対応表

| Dify ノード種 | 使用ワークフロー |
|--------------|-----------------|
| knowledge-retrieval | CMN-01, 05, 06 |
| question-classifier | CMN-05, 10 |
| parameter-extractor | CMN-03, 04, 08 |
| if-else | CMN-04, 06, 08, 10 |
| code | CMN-02, 03, 04, 06, 07, 08, 09, 10 |
| http-request | CMN-09 |
| template-transform | CMN-02, 03, 04, 06, 07, 08, 10 |
| variable-aggregator | CMN-03, 04, 08, 10 |
| iteration | CMN-09 |
| answer (Chatflow) | CMN-05 |

---

## 各ワークフロー詳細

### CMN-01: 社内規程・就業規則Q&A

**ファイル**: `cmn-01-social-rules-qa.yml`
**パターン**: RAG (Knowledge Retrieval → LLM)
**対象**: 総務部 / 全社員

就業規則・出張旅費規程・情報セキュリティポリシー等をナレッジベースに登録し、自然言語で質問できるワークフロー。規程名・条項番号を明示した回答を生成する。

```
開始 → 規程ナレッジ検索(KR) → 規程回答生成(LLM) → 終了
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `question` を入力 |
| 規程ナレッジ検索 | knowledge-retrieval | 社内規程KBから検索 (top_k: 5) |
| 規程回答生成 | llm | context有効、temp: 0.2 |
| 終了 | end | `answer` を出力 |

---

### CMN-02: 日報自動生成

**ファイル**: `cmn-02-daily-report-generator.yml`
**パターン**: Code → LLM → Template Transform
**対象**: 全部門

箇条書きメモ・対応時間・翌日予定を入力し、Code整形→LLM日報本文生成→Template Transformでヘッダー・フッター付与。

```
開始(3入力) → 入力整形(Code) → 日報生成(LLM) → 日報フォーマット(TT) → 終了
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `tasks_memo`, `hours_worked`, `tomorrow_plan` |
| 入力整形 | code | 3入力をセクションに整形 |
| 日報生成 | llm | 日報フォーマットに変換、temp: 0.5 |
| 日報フォーマット | template-transform | ヘッダー・フッター付与 |
| 終了 | end | `daily_report` を出力 |

---

### CMN-03: 議事録要約・アクションアイテム抽出

**ファイル**: `cmn-03-meeting-minutes.yml`
**パターン**: Parameter Extractor → 並列LLM → Variable Aggregator → Template Transform
**対象**: 全部門（管理職・PL）

会議テキストからPEでメタ情報抽出、並列LLMで「議事要約」と「アクションアイテム」を同時生成し、正式フォーマットに整形。

```
開始 → メタ情報抽出(PE) ─┬→ 議事要約(LLM) ────────┐
                          └→ アクションアイテム(LLM) ┤→ 結果統合(VA) → 議事録整形(TT) → 終了
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `meeting_text`, `meeting_type` |
| メタ情報抽出 | parameter-extractor | 日時、参加者、議題、会議名を抽出 |
| 議事要約 | llm | 議論ポイント・決定事項を要約 |
| アクションアイテム抽出 | llm | 担当者・期限付きToDoを抽出 |
| 結果統合 | variable-aggregator | 2つのLLM出力を統合 |
| 議事録整形 | template-transform | 正式議事録フォーマットに整形 |
| 終了 | end | `meeting_minutes` を出力 |

---

### CMN-04: 経費申請チェック

**ファイル**: `cmn-04-expense-check.yml`
**パターン**: PE → Code → IF/ELSE → LLM/TT → Variable Aggregator
**対象**: 経理部 / 全社員

経費申請テキストを構造化抽出し、職級別上限・カテゴリ別ルールでチェック。適合→LLM承認コメント、不適合→TT修正指示。

```
開始 → 経費情報抽出(PE) → 規程チェック(Code) → 適合判定(IF/ELSE)
                                                  ├─[PASS] → 承認コメント(LLM) ─┐
                                                  └─[FAIL] → 不適合通知(TT) ────┤→ 結果集約(VA) → 終了
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `expense_text`, `applicant_grade` (select) |
| 経費情報抽出 | parameter-extractor | 品目・金額・日付・カテゴリ・支払先を抽出 |
| 規程チェック | code | 職級別上限額・事前申請要否を判定 |
| 適合判定 | if-else | `result` が "PASS" → true |
| 承認コメント生成 | llm | 適合案件の承認推奨コメント |
| 不適合通知 | template-transform | 不適合理由と修正方法を整形 |
| 結果集約 | variable-aggregator | 両分岐を統合 |
| 終了 | end | `check_result` を出力 |

---

### CMN-05: 社内ヘルプデスクチャット

**ファイル**: `cmn-05-helpdesk-chat.yml`
**パターン**: Question Classifier(3分岐) → KR×2 → LLM(memory) → Answer
**対象**: 情報システム部 / 全社員
**モード**: **advanced-chat (Chatflow)**

社内IT・総務・人事の問い合わせを3分類し、IT/総務はナレッジ検索+LLM、人事はLLM直接回答。会話履歴を保持しマルチターン対応。

```
開始 → 問い合わせ分類(QC)
          ├─[IT系]   → ITナレッジ検索(KR) → IT対応LLM(memory) → IT回答(Answer)
          ├─[総務系] → 総務ナレッジ検索(KR) → 総務対応LLM(memory) → 総務回答(Answer)
          └─[人事系]                        → 人事対応LLM(memory) → 人事回答(Answer)
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | sys.query (Chatflow) |
| 問い合わせ分類 | question-classifier | IT系/総務系/人事系 3分類 |
| ITナレッジ検索 | knowledge-retrieval | IT FAQ KB検索 |
| 総務ナレッジ検索 | knowledge-retrieval | 総務規程KB検索 |
| IT対応LLM | llm | context + memory有効 |
| 総務対応LLM | llm | context + memory有効 |
| 人事対応LLM | llm | memory有効 |
| IT回答 | answer | IT系回答出力 |
| 総務回答 | answer | 総務系回答出力 |
| 人事回答 | answer | 人事系回答出力 |

---

### CMN-06: 契約書リスクレビュー

**ファイル**: `cmn-06-contract-review.yml`
**パターン**: 3層ガードパイプライン (Code → IF/ELSE → KR → LLM → Code → IF/ELSE)
**対象**: 法務部 / 営業部

入力検証(第1層)→ガイドラインKR検索+LLMリスク分析→出力検証(第3層)の3層ガード。不正入力・断定的法的助言を自動ブロック。

```
開始 → 入力検証(Code) → 入力判定(IE) ─[NG]→ 拒否応答(TT) → 終了
                                       ─[OK]→ ガイドライン検索(KR) → リスク分析(LLM)
                                                → 出力検証(Code) → 出力判定(IE) ─[OK]→ 終了
                                                                                ─[NG]→ 拒否応答(TT) → 終了
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `contract_text`, `contract_type` (select) |
| 入力検証 | code | 文字数・インジェクションパターン検出（第1層） |
| 入力判定 | if-else | is_valid == "true" |
| ガイドライン検索 | knowledge-retrieval | 契約レビューガイドラインKB |
| リスク分析 | llm | 5項目リスク分析、context有効、temp: 0.2 |
| 出力検証 | code | 断定的法的助言パターン検出（第3層） |
| 出力判定 | if-else | output_safe == "true" |
| 拒否応答 | template-transform | 安全な定型応答（入力NG/出力NG共用） |
| 終了 | end | `review_result` / `rejection_message` |

---

### CMN-07: 稟議書ドラフト作成（汎用版）

**ファイル**: `cmn-07-ringi-draft.yml`
**パターン**: 多入力 → Code → LLM(8192tok) → Template Transform
**対象**: 全部門 / 管理職

6つの入力（件名・区分・金額・目的・効果・リスク）から正式な稟議書ドラフトを自動生成。日本企業特有の決裁プロセスに対応。

```
開始(6入力) → 入力整形(Code) → 稟議書生成(LLM) → 稟議書フォーマット(TT) → 終了
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `subject`, `category` (select), `amount`, `purpose`, `expected_effect`, `risk_alternatives` |
| 入力整形 | code | 6入力を稟議書セクションに整形 |
| 稟議書生成 | llm | max_tokens: 8192、temp: 0.3 |
| 稟議書フォーマット | template-transform | 決裁欄・ヘッダー・フッター付与 |
| 終了 | end | `ringi_draft` を出力 |

---

### CMN-08: 採用候補者スクリーニング

**ファイル**: `cmn-08-resume-screening.yml`
**パターン**: PE → Code(スコアリング) → IF/ELSE → LLM/TT → Variable Aggregator
**対象**: 人事部

職務経歴書をPEで構造化し、ポジション別にスコアリング。60点以上→LLM詳細評価、60点未満→TT不合格フィードバック。

```
開始 → 候補者情報抽出(PE) → スコアリング(Code) → スコア判定(IF/ELSE)
                                                    ├─[60以上] → 評価コメント(LLM) ─┐
                                                    └─[60未満] → 不合格FB(TT) ──────┤→ 結果集約(VA) → 終了
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `resume_text`, `position` (select), `required_experience_years` |
| 候補者情報抽出 | parameter-extractor | 氏名・経験年数・スキル・学歴等を抽出 |
| スコアリング | code | 経験(40点)+スキル(40点)+学歴(20点)で合計100点 |
| スコア判定 | if-else | result == "PASS" (60点以上) |
| 評価コメント生成 | llm | 強み・懸念・面接確認ポイント |
| 不合格フィードバック | template-transform | スコアと不通過理由 |
| 結果集約 | variable-aggregator | 両分岐を統合 |
| 終了 | end | `screening_result` を出力 |

---

### CMN-09: 部門別KPIレポート一括生成

**ファイル**: `cmn-09-multi-department-report.yml`
**パターン**: Code → Iteration[HTTP] → Code → LLM
**対象**: 経営企画部

カンマ区切りの部門名リストからAPIで各部門KPIを一括取得し、LLMで部門横断の経営分析レポートを生成。

```
開始 → 部門配列化(Code) → 部門イテレーション ──→ 結果集約(Code) → 経営分析(LLM) → 終了
                              └─[KPI API(HTTP)]─┘
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `department_list`, `report_month` |
| 部門配列化 | code | カンマ区切り→配列+URLエンコード |
| 部門イテレーション | iteration | parallel_mode, continue-on-error |
| KPI API | http-request | GET `/kpi?dept={dept}&month={month}` |
| 結果集約 | code | API結果を集約しサマリテキスト生成 |
| 経営分析 | llm | 部門横断KPI分析レポート生成 |
| 終了 | end | `kpi_report` を出力 |

---

### CMN-10: 営業メール自動生成

**ファイル**: `cmn-10-sales-email-generator.yml`
**パターン**: Code → IF/ELSE → QC(4分岐) → LLM×4 → VA → Code
**対象**: 営業部

入力検証後、4種類の営業メール（新規アポ・フォロー・見積送付・お礼）を専用LLMで生成。日本のビジネスメール文化（敬語・時候の挨拶）に対応。

```
開始 → 入力検証(Code) → 入力判定(IE) ─[NG]→ エラー応答(TT) → 終了
                                       ─[OK]→ メール種別分類(QC)
                                                  ├─[新規アポ] → 新規アポメール(LLM) ─┐
                                                  ├─[フォロー] → フォローメール(LLM)  ─┤
                                                  ├─[見積送付] → 見積メール(LLM)      ─┤→ 結果集約(VA) → JSON構築(Code) → 終了
                                                  └─[お礼]     → お礼メール(LLM)     ─┘
```

| ノード | 種別 | 役割 |
|--------|------|------|
| 開始 | start | `email_context`, `recipient_name`, `company_name`, `email_type` (select) |
| 入力検証 | code | 必須項目・インジェクションチェック |
| 入力判定 | if-else | is_valid == "true" |
| エラー応答 | template-transform | エラーメッセージ |
| メール種別分類 | question-classifier | 4分岐: アポ/フォロー/見積/お礼 |
| 新規アポメール | llm | 新規アポイント依頼メール、temp: 0.5 |
| フォローメール | llm | 商談フォローメール、temp: 0.5 |
| 見積メール | llm | 見積送付メール、temp: 0.3 |
| お礼メール | llm | お礼メール、temp: 0.5 |
| 結果集約 | variable-aggregator | 4LLM出力を統合 |
| JSON構築 | code | json.dumps() で安全にJSON構築 |
| 終了 | end | `email_draft` / `error_message` |

---

## 利用方法

1. 各 `.yml` ファイルを Dify の **Import DSL** 機能でインポート
2. **ナレッジベース ID の差し替え**: `*-kb-placeholder` を実際の Dataset ID に置換
3. **LLM モデルの設定**: デフォルト `gpt-4o-mini` / `openai` を利用環境に合わせて変更
4. **環境変数の設定**: API キー等が必要な場合は `environment_variables` に追加
5. テスト実行後、プロンプトやルール閾値を業務要件に合わせて調整

## カスタマイズのポイント

| 項目 | 説明 |
|------|------|
| **経費上限額** | CMN-04 の Code ノード内 `grade_limits` を自社規程に合わせて変更 |
| **採用スコアリング** | CMN-08 の Code ノード内 `position_skills` にポジション別要件スキルを追加 |
| **QC 分類ルール** | CMN-05, CMN-10 の `instruction` に自社特有の分類ルールを追加 |
| **稟議書フォーマット** | CMN-07 の TT ノード内テンプレートを自社の稟議書書式に合わせて変更 |
| **契約レビュー基準** | CMN-06 のガイドラインKBに自社の契約レビュー基準書を登録 |
