# Dify Workflow ゴールデンルール

Difyワークフロー（DSL）を正しく生成・編集するための包括的リファレンス。

---

## 目次

1. [DSLファイル全体構造](#1-dslファイル全体構造)
2. [ノードの共通構造](#2-ノードの共通構造)
3. [エッジ（接続）の構造](#3-エッジ接続の構造)
4. [変数参照の構文](#4-変数参照の構文)
5. [全ノードタイプ詳細](#5-全ノードタイプ詳細)
6. [Workflow vs Chatflow の違い](#6-workflow-vs-chatflow-の違い)
7. [変数システム](#7-変数システム)
8. [代表的なワークフローパターン](#8-代表的なワークフローパターン)
9. [API連携](#9-api連携)
10. [ゴールデンルール（チェックリスト）](#10-ゴールデンルールチェックリスト)
11. [完全なDSLサンプル](#11-完全なdslサンプル)

---

## 1. DSLファイル全体構造

Dify DSL は YAML 形式。フロントエンドのキャンバス状態をそのままシリアライズしたもの。

```yaml
version: "0.1.4"                # DSLバージョン
kind: "app"                     # 常に "app"
app:
  name: "ワークフロー名"
  description: "説明"
  icon: "🤖"                    # 絵文字またはアイコン参照
  icon_background: "#FFEAD5"
  mode: "workflow"              # "workflow" | "advanced-chat" | "chat" | "agent-chat" | "completion"
  use_icon_as_answer_icon: false
workflow:
  graph:
    nodes: [...]                # ノード定義の配列
    edges: [...]                # ノード間の接続の配列
    viewport:
      x: 0
      y: 0
      zoom: 1
  features: {...}               # 機能トグル
  environment_variables: [...]  # 環境変数（APIキー等の秘密情報）
  conversation_variables: [...]  # 会話変数（Chatflowのみ）
```

### 必須フィールド

| フィールド | 必須 | 説明 |
|---|---|---|
| `app.name` | Yes | アプリ名 |
| `app.mode` | Yes | `workflow` または `advanced-chat` |
| `workflow.graph.nodes` | Yes | 最低限 Start + End（またはAnswer） |
| `workflow.graph.edges` | Yes | ノード間の接続 |

### features の構造

```yaml
features:
  file_upload:
    image:
      enabled: false
      number_limits: 3
      transfer_methods:
      - local_file
      - remote_url
  opening_statement: ''
  retriever_resource:
    enabled: false
  sensitive_word_avoidance:
    enabled: false               # 有効化する場合は下記「sensitive_word_avoidance 詳細」参照
  speech_to_text:
    enabled: false
  suggested_questions: []
  suggested_questions_after_answer:
    enabled: false
  text_to_speech:
    enabled: false
    language: ''
    voice: ''
```

### sensitive_word_avoidance 詳細

`config`（単数形）キーの直下にフラットな辞書を置くこと。`configs`（複数形）やリスト形式は不可。

```yaml
# キーワードフィルタ方式
sensitive_word_avoidance:
  enabled: true
  type: keywords                         # "keywords" | "openai_moderation" | "api"
  config:                                # ※ "configs" ではなく "config"（単数形）
    keywords: "爆弾\n殺害\n違法薬物"      # 改行区切りの文字列（リストではない）。最大100行、10000文字
    inputs_config:
      enabled: true
      preset_response: "お答えできません。"  # 最大100文字
    outputs_config:
      enabled: true
      preset_response: "回答を生成できませんでした。"  # 最大100文字

# OpenAI Moderation API 方式
sensitive_word_avoidance:
  enabled: true
  type: openai_moderation
  config:
    inputs_config:
      enabled: true
      preset_response: "コンテンツポリシー違反です。"
    outputs_config:
      enabled: true
      preset_response: "出力がブロックされました。"

# 外部API方式
sensitive_word_avoidance:
  enabled: true
  type: api
  config:
    api_based_extension_id: "your-extension-uuid"
    inputs_config:
      enabled: true
      preset_response: "コンテンツがブロックされました。"
    outputs_config:
      enabled: true
      preset_response: "出力がブロックされました。"
```

#### よくある間違い

| 誤り | 正しい形式 | 説明 |
|---|---|---|
| `configs:` (複数形) | `config:` (単数形) | Difyソースが `config` キーを参照する |
| `keywords:` をYAMLリスト (`- 爆弾`) で記述 | `keywords: "爆弾\n殺害"` | 改行区切りの単一文字列が必要 |
| `config:` の下にリスト (`- keywords:`) | `config:` の下にフラット辞書 | `config` は `dict` 型（リスト不可） |
| `preset_response` が100文字超 | 100文字以内に収める | バリデーションで弾かれる |

---

## 2. ノードの共通構造

すべてのノードは以下の共通フォーマットに従う。

```yaml
- id: '1714264983912'           # 一意のID（通常タイムスタンプ文字列）
  type: custom                   # 常に "custom"（React Flow用）
  data:
    type: start                  # Difyノードタイプ（後述）
    title: "ノードタイトル"       # キャンバス上の表示名
    desc: ''                     # オプションの説明
    selected: false              # UI状態
    # ... ノードタイプ固有の設定 ...
  position:
    x: 80                       # キャンバス上のX座標
    y: 282                      # キャンバス上のY座標
  positionAbsolute:
    x: 80
    y: 282
  height: 89                    # ノードの高さ
  width: 243                    # ノードの幅
  sourcePosition: right         # 出力ポートの位置
  targetPosition: left          # 入力ポートの位置
  selected: false
```

### ルール

- **`id`** は文字列で一意であること（タイムスタンプが一般的）
- **`type`** は常に `custom`（`data.type` がDifyのノード種類を示す）
- **`position`** と **`positionAbsolute`** は同じ値にするのが安全
- ノード間の間隔は X方向に 300px 程度が見やすい

---

## 3. エッジ（接続）の構造

```yaml
- id: "sourceId-targetId"        # 一般的に "ソースID-ターゲットID"
  source: '1714264983912'        # ソースノードのID
  sourceHandle: source           # 出力ポート名
  target: '1714264986101'        # ターゲットノードのID
  targetHandle: target           # 入力ポート名（常に "target"）
  type: custom                   # 常に "custom"
  data:
    sourceType: start            # ソースノードの data.type
    targetType: llm              # ターゲットノードの data.type
    isInIteration: false         # イテレーション内かどうか
```

### ルール

- **`sourceHandle`**: 通常は `source`。条件分岐ノード（IF/ELSE、Question Classifier）では条件に応じたハンドル名を使用
- **`targetHandle`**: 常に `target`
- **`data.sourceType`** と **`data.targetType`** は対応するノードの `data.type` と一致させること
- 循環参照は不可（DAG: 有向非巡回グラフ）

### IF/ELSE ノードのエッジ例

```yaml
# IF条件がtrueの場合
- source: 'ifelse_node_id'
  sourceHandle: 'true'           # または条件IDに対応するハンドル
  target: 'true_branch_node_id'
  targetHandle: target

# ELSE の場合
- source: 'ifelse_node_id'
  sourceHandle: 'false'
  target: 'false_branch_node_id'
  targetHandle: target
```

### Question Classifier ノードのエッジ例

```yaml
# 各分類クラスごとにエッジを作成
- source: 'classifier_node_id'
  sourceHandle: 'class_1'        # クラスIDをハンドルとして使用
  target: 'branch_a_node_id'
  targetHandle: target
```

---

## 4. 変数参照の構文

### 3つの参照方法

| 使用場所 | 構文 | 例 |
|---|---|---|
| プロンプトテンプレート内 | `{{#NODE_ID.variable_name#}}` | `{{#1714264983912.query#}}` |
| value_selector（YAML配列） | `[NODE_ID, variable_name]` | `['1714264986101', 'text']` |
| HTTPリクエストのbody/URL | `{{variable_name}}` | `{{api_response.data}}` |

### value_selector の書き方

```yaml
# 直前のノードの出力を参照
value_selector:
- '1714264986101'          # ノードID
- text                     # 変数名

# システム変数を参照
value_selector:
- sys
- query
```

### プロンプトテンプレートでの参照

```yaml
prompt_template:
- role: system
  text: "あなたは親切なアシスタントです。"
- role: user
  text: '{{#1714264983912.query#}}'    # Start ノードの query 変数
```

### ルール

- `{{#...#}}` 内のノードIDは必ず存在するノードのIDであること
- 参照先ノードは DAG 上で上流（前方）にあること
- 変数名は参照先ノードの出力変数として定義されていること

---

## 5. 全ノードタイプ詳細

### 5.1 Start ノード (`start`)

ワークフローの入口。ユーザー入力変数を定義する。

```yaml
data:
  type: start
  title: "開始"
  variables:
  - label: "ユーザークエリ"
    variable: query
    type: paragraph            # 入力タイプ
    required: true
    max_length: 999999
    options: []                # select タイプの場合のみ
```

#### 入力変数タイプ

| タイプ | 説明 | 制約 |
|---|---|---|
| `text` | 短いテキスト入力 | 最大256文字 |
| `paragraph` | 長文テキスト入力 | 制限なし（max_length で指定可） |
| `select` | ドロップダウン選択 | `options` 配列に選択肢を定義 |
| `number` | 数値入力 | - |
| `checkbox` | ブール値（true/false） | - |
| `object` | JSON オブジェクト | - |
| `single-file` | ファイルアップロード（単一） | - |
| `file-list` | ファイルアップロード（複数） | - |

---

### 5.2 End ノード (`end`)

**Workflow モード専用**。最終出力を定義する。

```yaml
data:
  type: end
  title: "終了"
  outputs:
  - variable: result
    value_selector:
    - '1714264986101'
    - text
```

---

### 5.3 Answer ノード (`answer`)

**Chatflow モード専用**。ストリーミング応答を定義する。

```yaml
data:
  type: answer
  title: "応答"
  answer: "{{#LLM_NODE_ID.text#}}"
```

- 複数箇所に配置可能
- ストリーミング出力に対応

---

### 5.4 LLM ノード (`llm`)

大規模言語モデルを呼び出す中核ノード。

```yaml
data:
  type: llm
  title: "LLM"
  model:
    provider: openai
    name: gpt-4o-mini
    mode: chat                   # chat | completion
    completion_params:
      temperature: 0.7           # 0〜2（推奨: 0〜1）
      top_p: 1
      max_tokens: 512
      frequency_penalty: 0
      presence_penalty: 0
  prompt_template:
  - role: system
    text: "あなたは親切なアシスタントです。"
  - role: user
    text: '{{#1714264983912.query#}}'
  context:
    enabled: false               # ナレッジコンテキストの注入
    variable_selector: []
  memory:
    enabled: false               # 会話履歴（Chatflowのみ）
    window:
      enabled: true
      size: 10
    role_prefix:
      user: "Human"
      assistant: "AI"
  vision:
    enabled: false               # 画像・ファイル処理
  variables: []
```

#### 出力変数

| 変数 | 説明 |
|---|---|
| `text` | LLM の生成テキスト |

#### モデル設定のプリセット

| プリセット | temperature | 用途 |
|---|---|---|
| Creative | 0.8〜1.0 | 創造的なコンテンツ生成 |
| Balanced | 0.5〜0.7 | 汎用的な応答 |
| Precise | 0.0〜0.3 | 正確性重視の応答 |

---

### 5.5 Knowledge Retrieval ノード (`knowledge-retrieval`)

ナレッジベースから関連文書を検索する。

```yaml
data:
  type: knowledge-retrieval
  title: "ナレッジ検索"
  query_variable_selector:
  - '1714264983912'
  - query
  dataset_ids:
  - "dataset-uuid-1"
  - "dataset-uuid-2"
  retrieval_mode: multiple       # single | multiple
  multiple_retrieval_config:
    top_k: 3
    score_threshold: 0.5
    reranking_model:
      provider: cohere
      name: rerank-english-v2.0
  single_retrieval_config:       # single モードの場合
    model:
      provider: openai
      name: gpt-4
```

#### 検索戦略

| モード | 説明 |
|---|---|
| `single` (N-to-1) | LLM が最適なナレッジベースを選択して検索 |
| `multiple` (Multi-way) | 全ナレッジベースを検索し、Rerankモデルで最適化 |

#### 出力変数

| 変数 | 説明 |
|---|---|
| `result` | 検索結果のチャンクリスト |

---

### 5.6 IF/ELSE ノード (`if-else`)

条件分岐。複数の ELIF ブランチにも対応。

```yaml
data:
  type: if-else
  title: "条件分岐"
  conditions:
  - id: condition_1
    variable_selector:
    - '1714264983912'
    - query
    comparison_operator: contains
    value: "keyword"
  logical_operator: and          # and | or
```

#### 比較演算子

| 演算子 | 説明 | 対応型 |
|---|---|---|
| `contains` | 含む | String |
| `not-contains` | 含まない | String |
| `starts-with` | 〜で始まる | String |
| `ends-with` | 〜で終わる | String |
| `is` | 等しい | String, Number |
| `is-not` | 等しくない | String, Number |
| `empty` | 空 | String |
| `not-empty` | 空でない | String |
| `>`, `<`, `>=`, `<=` | 数値比較 | Number |

#### エッジの sourceHandle

- `true`: IF条件が真の場合のブランチ
- `false`: ELSE のブランチ

---

### 5.7 Question Classifier ノード (`question-classifier`)

LLM を使った入力の分類・ルーティング。

```yaml
data:
  type: question-classifier
  title: "質問分類"
  query_variable_selector:
  - sys
  - query
  model:
    provider: openai
    name: gpt-4
  classes:
  - id: class_1
    name: "製品に関する質問"
  - id: class_2
    name: "請求に関する質問"
  - id: class_3
    name: "その他"
  instructions: "質問の主な意図に基づいて分類してください。"
  memory:
    enabled: true
    window:
      enabled: true
      size: 5
```

#### 出力変数

| 変数 | 説明 |
|---|---|
| `class_name` | マッチした分類ラベル |

#### エッジ

各 class の `id` を `sourceHandle` として使用。

---

### 5.8 Code ノード (`code`)

Python 3 または JavaScript コードを実行する。

```yaml
data:
  type: code
  title: "コード実行"
  code_language: python3         # python3 | javascript
  code: |
    def main(input_var: str) -> dict:
        import json
        data = json.loads(input_var)
        return {'result': data['key']}
  variables:
  - variable: input_var
    value_selector:
    - '1714264986101'
    - text
  outputs:
    result:
      type: string
```

#### 制約

- サンドボックス環境で実行（ファイルシステム、ネットワーク、OS操作不可）
- リトライ: 最大10回、最大5000ms間隔
- 必ず `main` 関数を定義し、`dict` を返すこと
- 使用可能なライブラリは組み込みモジュールに限定

---

### 5.9 HTTP Request ノード (`http-request`)

外部 API を呼び出す。

```yaml
data:
  type: http-request
  title: "API呼び出し"
  method: post                   # get | post | put | patch | delete | head
  url: "https://api.example.com/endpoint"
  headers:
    Content-Type: application/json
    Authorization: "Bearer {{#ENV.api_key#}}"
  params: {}
  body:
    type: json                   # json | form-data | binary | raw-text
    data: '{"query": "{{#NODE_ID.variable#}}"}'
  authorization:
    type: api-key                # no-auth | basic | bearer | custom
    config:
      api_key: "{{#ENV.api_key#}}"
  timeout:
    connect: 10000               # 接続タイムアウト（ms）
    read: 60000                  # 読み取りタイムアウト（ms）
    write: 20000                 # 書き込みタイムアウト（ms）
  retry:
    max_retries: 3               # 最大10
    retry_interval: 1000         # 最大5000ms
  ssl_verify: true
```

#### 出力変数

| 変数 | 説明 |
|---|---|
| `body` | レスポンスボディ |
| `status_code` | HTTPステータスコード |
| `headers` | レスポンスヘッダー |
| `files` | レスポンスファイル |
| `size` | レスポンスサイズ |

---

### 5.10 Template Transform ノード (`template-transform`)

Jinja2 テンプレートによるテキスト変換。

```yaml
data:
  type: template-transform
  title: "テンプレート変換"
  template: |
    {% for item in chunks %}
    ## {{ item.title | default('無題') }}
    {{ item.content }}
    スコア: {{ item.score }}
    ---
    {% endfor %}
  variables:
  - variable: chunks
    value_selector:
    - '1714264986101'
    - result
```

#### 出力変数

| 変数 | 説明 |
|---|---|
| `output` | テンプレート適用後のテキスト |

---

### 5.11 Variable Aggregator ノード (`variable-aggregator`)

複数ブランチの変数を1つに統合する。

```yaml
data:
  type: variable-aggregator
  title: "変数集約"
  variables:
  - - 'branch_a_node_id'
    - text
  - - 'branch_b_node_id'
    - text
  output_type: string
  advanced_settings:
    group_enabled: false
```

---

### 5.12 Variable Assigner ノード (`variable-assigner`)

会話変数やループ変数に値を書き込む。

```yaml
data:
  type: variable-assigner
  title: "変数代入"
  assignments:
  - target:
    - conversation_variable_name
    operation: overwrite
    source:
    - '1714264986101'
    - text
```

#### 操作タイプ

| 型 | 使用可能な操作 |
|---|---|
| String | `overwrite`, `clear`, `set` |
| Number | `overwrite`, `clear`, `set`, `add`, `subtract`, `multiply`, `divide` |
| Object | `overwrite`, `clear`, `set` |
| Array | `overwrite`, `clear`, `append`, `extend` |

---

### 5.13 Iteration ノード (`iteration`)

配列の各要素に対してループ処理を行う。

```yaml
data:
  type: iteration
  title: "イテレーション"
  iterator_selector:
  - '1714264986101'
  - array_variable             # Array型の変数
  output_selector:
  - INNER_NODE_ID
  - result
  parallel_mode: true           # 最大10並列
  error_handle_mode: continue-on-error
    # terminated: エラー時に停止
    # continue-on-error: エラーをスキップして継続
    # remove-abnormal-output: 異常出力を除外
  start_node_id: 'INNER_FIRST_NODE_ID'  # 必須: イテレーション内の最初に実行する子ノードのID
```

#### ループ内で使用可能な組み込み変数

| 変数 | 説明 |
|---|---|
| `items` | 現在の要素 |
| `index` | 現在のイテレーション番号 |

---

### 5.14 Parameter Extractor ノード (`parameter-extractor`)

LLM を使って入力テキストから構造化パラメータを抽出する。

```yaml
data:
  type: parameter-extractor
  title: "パラメータ抽出"
  model:
    provider: openai
    name: gpt-4
  query_variable_selector:
  - '1714264986101'
  - text
  parameters:
  - name: order_number
    type: string
    description: "注文番号"
    required: true
  - name: issue_type
    type: string
    description: "問題の種類: 返金、交換、追跡"
    required: true
  instruction: "顧客メッセージから注文番号と問題の種類を抽出してください。"
```

---

### 5.15 Agent ノード (`agent`) — v1.0+

自律的な推論とツール呼び出しを行うエージェント。

```yaml
data:
  type: agent
  title: "エージェント"
  model:
    provider: anthropic
    name: claude-3-5-sonnet
  agent_strategy: function_calling   # function_calling | react
  tools:
  - tool_name: web_search
    tool_parameters: {}
  instruction: "トピックを調査して包括的な回答を提供してください。"
  query_variable_selector:
  - '1714264983912'
  - query
  max_iterations: 10
```

#### 推論戦略

| 戦略 | 説明 |
|---|---|
| `function_calling` | 定義された関数を呼び出す構造化アプローチ |
| `react` | Reason + Act サイクルを交互に行う（推論過程が可視化される） |

---

### 5.16 Trigger ノード — v1.10+

#### Schedule Trigger (`trigger-schedule`)

```yaml
data:
  type: trigger-schedule
  # Cron形式で時間ベースの自動実行を設定
```

#### Webhook Trigger (`trigger-webhook`)

```yaml
data:
  type: trigger-webhook
  # 一意のHTTP URLを生成。リクエストパラメータが変数になる
```

#### Plugin Trigger (`trigger-plugin`)

```yaml
data:
  type: trigger-plugin
  # サードパーティアプリのイベントをサブスクライブ
```

> **注意**: トリガーのデータはDSLエクスポート時にセキュリティ上の理由でクリアされる。

---

## 6. Workflow vs Chatflow の違い

| 項目 | Workflow (`workflow`) | Chatflow (`advanced-chat`) |
|---|---|---|
| 実行方式 | シングルターン（1回の呼び出し） | マルチターン（会話型） |
| 開始ノード | `start`（カスタム入力変数を定義） | `start`（`sys.query` が自動的に利用可能） |
| 出力ノード | `end`（最終結果を返す） | `answer`（ストリーミング応答） |
| 状態管理 | ステートレス | 会話変数で状態を保持 |
| メモリ機能 | なし | LLMノードで会話履歴を参照可能 |
| API エンドポイント | `POST /v1/workflows/run` | `POST /v1/chat-messages` |
| ユースケース | バックエンド自動化、データパイプライン | チャットボット、カスタマーサービス |

---

## 7. 変数システム

### 7.1 システム変数

**Workflow 共通**:

| 変数 | 型 | 説明 |
|---|---|---|
| `sys.files` | Array[File] | ユーザーがアップロードしたファイル |
| `sys.user_id` | String | ユーザー識別子 |
| `sys.app_id` | String | アプリケーション識別子 |
| `sys.workflow_id` | String | ワークフロー識別子 |
| `sys.workflow_run_id` | String | 実行ランID |

**Chatflow 追加**:

| 変数 | 型 | 説明 |
|---|---|---|
| `sys.query` | String | ユーザーのチャット入力 |
| `sys.dialogue_count` | Number | 会話ターン数 |
| `sys.conversation_id` | String | セッション識別子 |

### 7.2 環境変数

```yaml
environment_variables:
- name: api_key
  type: secret                   # String | Number | Secret
  value: "sk-xxx..."
```

- 全ノードからグローバルに参照可能
- 実行中に変更不可
- `Secret` 型はDSLエクスポート時にマスクされる

### 7.3 会話変数（Chatflow のみ）

```yaml
conversation_variables:
- name: user_preference
  type: string                   # String | Number | Object | Array[string] | Array[number] | Array[object]
  value: ""
```

- ターンをまたいで状態を保持
- **Variable Assigner ノード** でのみ書き込み可能

---

## 8. 代表的なワークフローパターン

### パターン1: シンプル QA

```
Start → LLM → End
```

最も基本的な構成。ユーザーの質問に LLM が直接回答する。

### パターン2: RAG（検索拡張生成）

```
Start → Knowledge Retrieval → LLM（context有効） → End
```

ナレッジベースから関連文書を取得し、LLM のプロンプトにコンテキストとして注入する。

### パターン3: インテント分類 + ルーティング

```
Start → Question Classifier → [分類A: Knowledge Retrieval → LLM → End]
                             → [分類B: HTTP Request → Template → End]
                             → [分類C: LLM（汎用） → End]
```

ユーザーの意図を分類し、それぞれ最適な処理パスに振り分ける。

### パターン4: 並列処理 + 集約

```
Start → [並列ブランチ1: LLM（モデルA）]
      → [並列ブランチ2: LLM（モデルB）]
      → [並列ブランチ3: LLM（モデルC）]
      → Variable Aggregator → Template Transform → End
```

最大10並列ブランチ。複数モデルの結果を比較・統合する。

### パターン5: データパイプライン

```
Start → HTTP Request（データ取得） → Code（JSON解析） → Iteration [Template Transform] → LLM（要約） → End
```

外部 API からデータを取得し、変換・要約するバッチ処理。

### パターン6: ディープリサーチ

```
Start → LLM（計画立案） → Iteration [Agent（検索） → LLM（合成）] → LLM（最終レポート） → End
```

Agent ノードによる自律的な反復調査。

### パターン7: カスタマーサービス（Chatflow）

```
Start → Question Classifier → Knowledge Retrieval → LLM（memory有効）
                             → Parameter Extractor → HTTP Request（CRM） → LLM → Variable Assigner → Answer
```

会話変数で顧客情報を保持しながら対応する。

### パターン8: イベント駆動自動化（v1.10+）

```
Webhook Trigger → Code（バリデーション） → IF/ELSE → [処理パス: LLM → HTTP Request（Slack通知）]
                                                    → [拒否パス: End]
```

---

## 9. API連携

### ワークフロー実行 API

```
POST /v1/workflows/run
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "inputs": {
    "query": "ユーザーの質問"
  },
  "response_mode": "blocking",   // "blocking" | "streaming"
  "user": "user-id-123"
}
```

#### レスポンス（blocking モード）

```json
{
  "workflow_run_id": "uuid",
  "task_id": "uuid",
  "data": {
    "id": "uuid",
    "workflow_id": "uuid",
    "status": "succeeded",
    "outputs": {"result": "回答テキスト..."},
    "error": null,
    "elapsed_time": 3.45,
    "total_tokens": 1250,
    "total_steps": 5,
    "created_at": 1705395332,
    "finished_at": 1705395335
  }
}
```

#### ストリーミングモード

`response_mode: "streaming"` の場合、SSE（Server-Sent Events）形式で逐次レスポンスが返る。

### Chatflow 実行 API

```
POST /v1/chat-messages
Authorization: Bearer {api_key}
Content-Type: application/json

{
  "inputs": {},
  "query": "ユーザーのメッセージ",
  "response_mode": "streaming",
  "conversation_id": "",          // 空文字列で新規会話開始
  "user": "user-id-123"
}
```

---

## 10. ゴールデンルール（チェックリスト）

### 構造に関するルール

1. **必ず1つの Start ノード（または Trigger ノード）から開始すること**
2. **Workflow モードでは `end` ノード、Chatflow モードでは `answer` ノードで終了すること**
3. **循環参照（ループ）は不可** — グラフは DAG（有向非巡回グラフ）であること
4. **すべてのノードは一意の `id`（文字列）を持つこと**
5. **すべてのエッジの `source` と `target` は存在するノードIDを指すこと**
6. **ノードの `type` フィールドは常に `custom` にすること**（`data.type` が実際のノード種類）
7. **分岐後は Variable Aggregator で合流させること**（複数パスの結果を統合する場合）

### 変数に関するルール

8. **変数参照は上流ノードのみ** — DAG上で自分より前のノードの出力のみ参照可能
9. **プロンプト内の変数は `{{#NODE_ID.variable#}}` 形式を使用すること**
10. **value_selector は配列形式 `[NODE_ID, variable_name]` を使用すること**
11. **環境変数にAPIキーやシークレットを格納し、ノード内にハードコードしないこと**
12. **会話変数の書き込みは Variable Assigner ノードのみで行うこと**

### LLM ノードに関するルール

13. **`model.provider` と `model.name` は Dify インスタンスで設定済みのモデルを指定すること**
14. **`prompt_template` は `role` と `text` のペアのリストであること**
15. **`temperature` は用途に応じて適切に設定すること**（正確性重視: 0〜0.3、バランス: 0.5〜0.7、創造性: 0.8〜1.0）
16. **`max_tokens` は十分な値を設定すること**（短すぎると回答が途中で切れる）

### エッジに関するルール

17. **`data.sourceType` と `data.targetType` は接続先ノードの `data.type` と一致させること**
18. **IF/ELSE のエッジでは `sourceHandle` に `true` / `false` を使用すること**
19. **Question Classifier のエッジでは `sourceHandle` にクラスの `id` を使用すること**
20. **`targetHandle` は常に `target` であること**

### 設計に関するルール

21. **1つのノードには1つの責務** — 複雑な処理は複数ノードに分割すること
22. **エラーハンドリングを設計すること** — HTTP Request や Code ノードにはリトライ戦略を設定
23. **並列ブランチは最大10本**、ネスト深度は最大3レベル
24. **Iteration ノードには `start_node_id` を必ず指定すること** — 子ノードの実行開始点がないと実行されない
25. **Iteration の並列実行は最大10並列**
25. **ノードのタイトルは処理内容がわかる名前にすること**（「LLM」ではなく「回答を生成」など）
26. **Code ノードのサンドボックス制約を理解すること** — ファイルI/O、ネットワーク、OS操作は不可
27. **HTTP Request の URL にユーザー入力値を埋め込む場合は事前に URL エンコードすること** — Code ノードで `urllib.parse.quote()` を使い、エンコード済み変数を HTTP Request に渡す。Iteration で配列要素を URL に使う場合も、配列生成時にエンコード済みの値を格納すること（日本語・空白・`&` 等がクエリを破壊する）
28. **HTTP Request の JSON Body に LLM 出力を埋め込む場合は Code ノードで `json.dumps()` を使うこと** — LLM 出力に改行・引用符が含まれると不正 JSON になるため、テンプレート直接埋め込みは避ける
29. **IF/ELSE で LLM 判定結果に基づいて分岐する場合は Code ノードで構造化抽出してから厳密一致で判定すること** — LLM 自由文に `contains` を使うと否定文や説明文で誤検知する。Code で正規表現抽出し `is` で比較する
30. **Iteration 内のループ要素は `{{#ITERATION_NODE_ID.item#}}` で参照する** — `.item`（単数形）が現在の反復要素を返す。`.items`（複数形）は配列全体を参照するため使わないこと
31. **API レスポンスの数値フィールドは Code ノードで明示的に型変換すること** — API が文字列 `"12000000"` を返す場合、`float()` で変換しないと後続の数値比較（IF/ELSE の `>` 条件等）が失敗する。変換失敗時は `0` にフォールバックせず即エラー（`FAIL`）を返すこと（`0` 扱いだと後続の閾値チェックをすり抜ける）
32. **Code ノードで文字列リストのマッチングを行う場合は完全一致を使うこと** — `substring in item`（部分一致）はスキル名 `git` が `digitization` に誤マッチする等の過大評価を引き起こす。`item == keyword` または正規化済みリストの `keyword in list`（完全一致）を使う

### 運用に関するルール

27. **プロンプト、ツール、データセットのバージョン管理を行うこと**
28. **各ノードの入出力をログに記録し、観測可能性を確保すること**
29. **テスト用の評価データセットを準備すること**
30. **ワークフローを再利用可能なツールとして公開することを検討すること**（Workflow as Tool 機能）

---

## 11. 完全なDSLサンプル

### サンプル1: シンプルなQAワークフロー

```yaml
app:
  description: 'シンプルなQAワークフロー'
  icon: "\U0001F916"
  icon_background: '#FFEAD5'
  mode: workflow
  name: simple-qa-workflow
  use_icon_as_answer_icon: false
workflow:
  features:
    file_upload:
      image:
        enabled: false
        number_limits: 3
        transfer_methods:
        - local_file
        - remote_url
    opening_statement: ''
    retriever_resource:
      enabled: false
    sensitive_word_avoidance:
      enabled: false
    speech_to_text:
      enabled: false
    suggested_questions: []
    suggested_questions_after_answer:
      enabled: false
    text_to_speech:
      enabled: false
      language: ''
      voice: ''
  environment_variables: []
  conversation_variables: []
  graph:
    edges:
    - data:
        sourceType: start
        targetType: llm
      id: '1000000000001-1000000000002'
      source: '1000000000001'
      sourceHandle: source
      target: '1000000000002'
      targetHandle: target
      type: custom
    - data:
        sourceType: llm
        targetType: end
      id: '1000000000002-1000000000003'
      source: '1000000000002'
      sourceHandle: source
      target: '1000000000003'
      targetHandle: target
      type: custom
    nodes:
    - data:
        desc: 'ユーザーからの入力を受け取る'
        selected: false
        title: 開始
        type: start
        variables:
        - label: query
          max_length: 999999
          options: []
          required: true
          type: paragraph
          variable: query
      height: 89
      id: '1000000000001'
      position:
        x: 80
        y: 282
      positionAbsolute:
        x: 80
        y: 282
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    - data:
        context:
          enabled: false
          variable_selector: []
        desc: 'クエリに基づいて回答を生成'
        model:
          completion_params:
            frequency_penalty: 0
            max_tokens: 1024
            presence_penalty: 0
            temperature: 0.7
            top_p: 1
          mode: chat
          name: gpt-4o-mini
          provider: openai
        prompt_template:
        - role: system
          text: "あなたは親切で知識豊富なアシスタントです。ユーザーの質問に対して、正確で分かりやすい回答を提供してください。"
        - role: user
          text: '{{#1000000000001.query#}}'
        selected: false
        title: 回答を生成
        type: llm
        variables: []
        vision:
          enabled: false
      height: 97
      id: '1000000000002'
      position:
        x: 380
        y: 282
      positionAbsolute:
        x: 380
        y: 282
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    - data:
        desc: ''
        outputs:
        - value_selector:
          - '1000000000002'
          - text
          variable: result
        selected: false
        title: 終了
        type: end
      height: 89
      id: '1000000000003'
      position:
        x: 680
        y: 282
      positionAbsolute:
        x: 680
        y: 282
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    viewport:
      x: 0
      y: 0
      zoom: 1
```

### サンプル2: RAG + 条件分岐ワークフロー

```yaml
app:
  description: 'ナレッジベースを活用した条件分岐付きワークフロー'
  icon: "\U0001F4DA"
  icon_background: '#E4FBCC'
  mode: workflow
  name: rag-conditional-workflow
  use_icon_as_answer_icon: false
workflow:
  features:
    file_upload:
      image:
        enabled: false
        number_limits: 3
        transfer_methods:
        - local_file
        - remote_url
    opening_statement: ''
    retriever_resource:
      enabled: true
    sensitive_word_avoidance:
      enabled: false
    speech_to_text:
      enabled: false
    suggested_questions: []
    suggested_questions_after_answer:
      enabled: false
    text_to_speech:
      enabled: false
      language: ''
      voice: ''
  environment_variables: []
  conversation_variables: []
  graph:
    edges:
    - data:
        sourceType: start
        targetType: question-classifier
      id: '2000000000001-2000000000002'
      source: '2000000000001'
      sourceHandle: source
      target: '2000000000002'
      targetHandle: target
      type: custom
    - data:
        sourceType: question-classifier
        targetType: knowledge-retrieval
      id: '2000000000002-2000000000003'
      source: '2000000000002'
      sourceHandle: class_1
      target: '2000000000003'
      targetHandle: target
      type: custom
    - data:
        sourceType: question-classifier
        targetType: llm
      id: '2000000000002-2000000000005'
      source: '2000000000002'
      sourceHandle: class_2
      target: '2000000000005'
      targetHandle: target
      type: custom
    - data:
        sourceType: knowledge-retrieval
        targetType: llm
      id: '2000000000003-2000000000004'
      source: '2000000000003'
      sourceHandle: source
      target: '2000000000004'
      targetHandle: target
      type: custom
    - data:
        sourceType: llm
        targetType: end
      id: '2000000000004-2000000000006'
      source: '2000000000004'
      sourceHandle: source
      target: '2000000000006'
      targetHandle: target
      type: custom
    - data:
        sourceType: llm
        targetType: end
      id: '2000000000005-2000000000006'
      source: '2000000000005'
      sourceHandle: source
      target: '2000000000006'
      targetHandle: target
      type: custom
    nodes:
    - data:
        desc: ''
        selected: false
        title: 開始
        type: start
        variables:
        - label: query
          max_length: 999999
          options: []
          required: true
          type: paragraph
          variable: query
      height: 89
      id: '2000000000001'
      position:
        x: 80
        y: 282
      positionAbsolute:
        x: 80
        y: 282
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    - data:
        desc: '質問の種類を分類'
        title: 質問分類
        type: question-classifier
        query_variable_selector:
        - '2000000000001'
        - query
        model:
          provider: openai
          name: gpt-4o-mini
        classes:
        - id: class_1
          name: "ドキュメントに関する質問"
        - id: class_2
          name: "一般的な質問"
        instructions: "ユーザーの質問が社内ドキュメントや製品情報に関するものか、一般的な雑談・質問かを判断してください。"
      height: 160
      id: '2000000000002'
      position:
        x: 380
        y: 242
      positionAbsolute:
        x: 380
        y: 242
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    - data:
        desc: 'ナレッジベースから関連文書を検索'
        title: ナレッジ検索
        type: knowledge-retrieval
        query_variable_selector:
        - '2000000000001'
        - query
        dataset_ids:
        - "your-dataset-uuid-here"
        retrieval_mode: multiple
        multiple_retrieval_config:
          top_k: 3
          score_threshold: 0.5
      height: 120
      id: '2000000000003'
      position:
        x: 680
        y: 182
      positionAbsolute:
        x: 680
        y: 182
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    - data:
        context:
          enabled: true
          variable_selector:
          - '2000000000003'
          - result
        desc: 'ナレッジに基づいて回答を生成'
        model:
          completion_params:
            temperature: 0.3
            max_tokens: 1024
          mode: chat
          name: gpt-4o-mini
          provider: openai
        prompt_template:
        - role: system
          text: "以下のコンテキスト情報に基づいて、ユーザーの質問に正確に回答してください。コンテキストに含まれない情報については、「その情報は見つかりませんでした」と回答してください。"
        - role: user
          text: '{{#2000000000001.query#}}'
        title: ナレッジ回答
        type: llm
        variables: []
        vision:
          enabled: false
      height: 97
      id: '2000000000004'
      position:
        x: 980
        y: 182
      positionAbsolute:
        x: 980
        y: 182
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    - data:
        context:
          enabled: false
          variable_selector: []
        desc: '一般的な質問に回答'
        model:
          completion_params:
            temperature: 0.7
            max_tokens: 1024
          mode: chat
          name: gpt-4o-mini
          provider: openai
        prompt_template:
        - role: system
          text: "あなたは親切なアシスタントです。ユーザーの質問に分かりやすく回答してください。"
        - role: user
          text: '{{#2000000000001.query#}}'
        title: 一般回答
        type: llm
        variables: []
        vision:
          enabled: false
      height: 97
      id: '2000000000005'
      position:
        x: 680
        y: 362
      positionAbsolute:
        x: 680
        y: 362
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    - data:
        desc: ''
        outputs:
        - value_selector:
          - '2000000000004'
          - text
          variable: result
        - value_selector:
          - '2000000000005'
          - text
          variable: result
        selected: false
        title: 終了
        type: end
      height: 89
      id: '2000000000006'
      position:
        x: 1280
        y: 282
      positionAbsolute:
        x: 1280
        y: 282
      selected: false
      sourcePosition: right
      targetPosition: left
      type: custom
      width: 243
    viewport:
      x: 0
      y: 0
      zoom: 0.8
```

---

## 参考リソース

- [Dify 公式ドキュメント](https://docs.dify.ai/)
- [Dify GitHub リポジトリ](https://github.com/langgenius/dify)
- [Dify DSL フォーマット議論 (#8090)](https://github.com/langgenius/dify/discussions/8090)
- [Dify ブログ — ワークフロー紹介](https://dify.ai/blog/dify-ai-workflow)
- [Awesome Dify Workflow（コミュニティ集）](https://github.com/svcvit/Awesome-Dify-Workflow)
- [Dify レガシードキュメント](https://legacy-docs.dify.ai/guides/workflow/node)
