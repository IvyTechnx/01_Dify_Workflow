#!/usr/bin/env python3
"""全50ワークフローの定義と生成"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gen_core import *

def V(name, vtype, required=True, options=None, ml=None):
    return make_var(name, vtype, required, options, ml)

def build(cat, num, slug, name, icon, bg, desc, vars_, main_var, sys_p, usr_p, out_t):
    dsl = gen_workflow(num, slug, name, icon, bg, desc, vars_, main_var, sys_p, usr_p, out_t)
    save_workflow(cat, num, slug, dsl)

# ═══ CROSS-FUNCTIONAL (121-130) ═══
print("=== Cross-Functional ===")

build('cross-functional', 121, 'document-proofreading', 'AI文書校正・品質改善', '✏️', '#E3F2FD',
    'ビジネス文書の誤字脱字・文法・表現・トーンを分析しスコア付きで改善提案を行う。Grammarly/文賢に相当する機能。',
    [V('document_text','paragraph'), V('document_type','select',True,['ビジネスメール','報告書','提案書','プレスリリース']),
     V('tone','select',True,['フォーマル','カジュアル','ニュートラル'])],
    'document_text',
    '''あなたはプロの日本語校正エディターです。以下の観点で文書を分析し、改善提案を行ってください。

## 分析項目
1. **誤字脱字チェック**: 漢字・送り仮名・カタカナ表記の誤り
2. **文法チェック**: 助詞の誤用・主述の不一致・修飾語の係り受け
3. **表現改善**: 冗長表現・曖昧表現・二重否定の修正
4. **トーン調整**: 指定されたトーンへの統一
5. **読みやすさ**: 一文の長さ・段落構成・箇条書きの活用

## 出力フォーマット
### 品質スコア（100点満点）
| 項目 | スコア | 評価 |
|------|--------|------|
| 正確性 | XX/25 | ○/△/× |
| 文法 | XX/25 | ○/△/× |
| 表現力 | XX/25 | ○/△/× |
| 読みやすさ | XX/25 | ○/△/× |
| **合計** | **XX/100** | |

### 修正箇所一覧
（行番号・元の表現・修正案・理由を表形式で）

### 改善後の文書（全文）''',
    '文書タイプ: {{#' + nid(121,1) + '.document_type#}}\nトーン: {{#' + nid(121,1) + '.tone#}}\n\n校正対象の文書:\n{{#' + nid(121,1) + '.document_text#}}',
    'AI文書校正レポート')

build('cross-functional', 122, 'sales-call-analysis', '商談録音AI分析・コーチング', '🎙️', '#FFF3E0',
    '商談の文字起こしテキストを入力し、トーク比率・キーワード・ネクストアクション・コーチングポイントを分析する。',
    [V('transcript_text','paragraph'), V('deal_stage','select',True,['初回商談','提案','クロージング','フォロー'])],
    'transcript_text',
    '''あなたは営業コーチングの専門家です。商談の文字起こしを分析し、以下の観点でフィードバックを提供してください。

## 分析項目
1. **トーク比率分析**: 営業担当 vs 顧客の発話量比率（理想: 営業40% / 顧客60%）
2. **ヒアリング品質**: BANT/MEDDIC情報の取得状況
3. **キーワード分析**: 顧客が言及した課題・ニーズ・競合・予算に関するキーワード
4. **異議への対応**: 顧客の懸念に対する応答の質
5. **ネクストアクション**: 合意されたネクストステップの明確さ

## 出力フォーマット
### 商談サマリー
### トーク分析
### キーワード・シグナル一覧
### コーチングポイント（良い点3つ・改善点3つ）
### 推奨ネクストアクション''',
    '商談ステージ: {{#' + nid(122,1) + '.deal_stage#}}\n\n商談文字起こし:\n{{#' + nid(122,1) + '.transcript_text#}}',
    '商談AI分析レポート')

build('cross-functional', 123, 'multilingual-localization', '多言語翻訳・ローカライズ', '🌐', '#E8F5E9',
    '文化的コンテキストを考慮したローカライズ翻訳を行う。DeepL/WOVNに相当する機能。',
    [V('source_text','paragraph'), V('source_lang','select',True,['日本語','英語','中国語','韓国語']),
     V('target_lang','select',True,['英語','日本語','中国語','韓国語']), V('context','text-input',False)],
    'source_text',
    '''あなたはプロの翻訳者兼ローカライゼーション専門家です。単なる逐語訳ではなく、ターゲット言語の文化・慣習に合わせたローカライズ翻訳を行ってください。

## ルール
1. 意味の正確性を最優先にしつつ、自然な表現にする
2. 専門用語はターゲット言語での標準的な訳語を使用
3. 文化的に不適切な表現やニュアンスの違いは注記する
4. 固有名詞・ブランド名は原則そのまま保持
5. 敬語レベルは原文のフォーマリティに合わせる

## 出力フォーマット
### 翻訳結果
（ローカライズされた翻訳文）

### 翻訳ノート
- 文化的適応を行った箇所の説明
- 代替表現の候補
- 注意が必要な表現''',
    '原文言語: {{#' + nid(123,1) + '.source_lang#}}\n翻訳先言語: {{#' + nid(123,1) + '.target_lang#}}\nコンテキスト: {{#' + nid(123,1) + '.context#}}\n\n原文:\n{{#' + nid(123,1) + '.source_text#}}',
    '多言語ローカライズ結果')

build('cross-functional', 124, 'invoice-journal-entry', '請求書AI読取→仕訳提案', '🧾', '#FFF8E1',
    '請求書テキストから取引先・金額・勘定科目を抽出し仕訳ドラフトを生成する。',
    [V('invoice_text','paragraph'), V('accounting_standard','select',True,['日本基準','IFRS'])],
    'invoice_text',
    '''あなたは経理・会計の専門家です。請求書テキストから情報を抽出し、仕訳ドラフトを作成してください。

## 抽出項目
1. 取引先名  2. 請求日  3. 支払期日  4. 品目・明細  5. 税込金額・税抜金額・消費税額
6. 適用税率（10% or 8%）  7. インボイス番号（あれば）

## 仕訳ルール
- 勘定科目は日本基準の標準的な科目名を使用
- 消費税は税抜経理方式で仮払消費税を計上
- 複合仕訳の場合は明細ごとに分解

## 出力フォーマット
### 請求書情報サマリー
### 仕訳ドラフト
| 借方科目 | 借方金額 | 貸方科目 | 貸方金額 | 摘要 |
### 注意事項・確認ポイント''',
    '会計基準: {{#' + nid(124,1) + '.accounting_standard#}}\n\n請求書テキスト:\n{{#' + nid(124,1) + '.invoice_text#}}',
    '仕訳ドラフト')

build('cross-functional', 125, 'brand-monitoring', 'SNSブランドモニタリング', '📱', '#F3E5F5',
    'ブランドに関するSNSデータを分析し、言及分析・感情推移・リスク検知レポートを生成する。',
    [V('brand_name','text-input'), V('monitoring_period','select',True,['直近1週間','直近1ヶ月','直近3ヶ月']),
     V('sns_data','paragraph')],
    'sns_data',
    '''あなたはソーシャルリスニングの専門家です。SNSデータを分析し、ブランドの評判・トレンド・リスクを包括的にレポートしてください。

## 分析項目
1. **言及量分析**: 期間内のメンション数・推移トレンド
2. **感情分析**: ポジティブ/ネガティブ/ニュートラルの比率と推移
3. **トピック分析**: 頻出キーワード・話題のクラスタリング
4. **インフルエンサー特定**: 影響力の大きいアカウントの特定
5. **リスク検知**: 炎上の兆候・ネガティブバズの早期発見
6. **競合比較**: 業界内でのSOV（Share of Voice）推定

## 出力フォーマット
### エグゼクティブサマリー
### 定量データ（表・グラフ推奨値）
### リスクアラート（ある場合）
### 推奨アクション''',
    'ブランド名: {{#' + nid(125,1) + '.brand_name#}}\n分析期間: {{#' + nid(125,1) + '.monitoring_period#}}\n\nSNSデータ:\n{{#' + nid(125,1) + '.sns_data#}}',
    'ブランドモニタリングレポート')

build('cross-functional', 126, 'lead-scoring', 'リードスコアリング', '🎯', '#E8EAF6',
    'リード情報をスコアリングし優先対応リストを生成する。',
    [V('lead_info','paragraph'), V('scoring_criteria','select',True,['BANT','MEDDIC','CHAMP'])],
    'lead_info',
    '''あなたはB2Bセールスのリードスコアリング専門家です。指定されたフレームワークに基づきリード情報を評価してください。

## スコアリング基準
### BANT: Budget/Authority/Need/Timeline
### MEDDIC: Metrics/Economic Buyer/Decision Criteria/Decision Process/Identify Pain/Champion
### CHAMP: Challenges/Authority/Money/Prioritization

## 出力フォーマット
### リードスコアカード
| 評価項目 | スコア(1-5) | 根拠 |
### 総合スコア・ランク（A/B/C/D）
### 推奨アクション・優先順位
### 不足情報・次回確認事項''',
    'スコアリング基準: {{#' + nid(126,1) + '.scoring_criteria#}}\n\nリード情報:\n{{#' + nid(126,1) + '.lead_info#}}',
    'リードスコアリングレポート')

build('cross-functional', 127, 'rfp-response', 'RFP自動回答ジェネレーター', '📋', '#E0F2F1',
    'RFP質問項目に対し自社情報に基づいた根拠付き回答ドラフトを生成する。',
    [V('rfp_questions','paragraph'), V('company_info','paragraph'), V('product_info','paragraph')],
    'rfp_questions',
    '''あなたはRFP（提案依頼書）回答の専門家です。提供された自社・製品情報に基づき、各質問に対して説得力のある回答を作成してください。

## ルール
1. 各質問に対し、根拠を明示した具体的な回答を作成
2. 自社の強みを自然にアピールする
3. 回答できない質問は正直に「要確認」と記載
4. 差別化ポイントを明確に打ち出す

## 出力フォーマット
### 回答一覧
| Q# | 質問概要 | 回答 | 根拠・エビデンス | 差別化ポイント |
### 総合アピールポイント
### 要確認事項リスト''',
    'RFP質問:\n{{#' + nid(127,1) + '.rfp_questions#}}\n\n自社情報:\n{{#' + nid(127,1) + '.company_info#}}\n\n製品情報:\n{{#' + nid(127,1) + '.product_info#}}',
    'RFP回答ドラフト')

build('cross-functional', 128, 'esg-report', 'ESGレポート生成', '🌱', '#E8F5E9',
    'ESGデータからガイドライン準拠のレポートドラフトを生成する。',
    [V('esg_data','paragraph'), V('reporting_standard','select',True,['GRI','SASB','TCFD','統合報告']),
     V('fiscal_year','text-input')],
    'esg_data',
    '''あなたはESG・サステナビリティレポートの専門家です。指定されたガイドラインに準拠したレポートドラフトを作成してください。

## 構成
### E（環境）: CO2排出量・エネルギー使用量・廃棄物・水使用量
### S（社会）: 従業員数・ダイバーシティ・労災・地域貢献
### G（ガバナンス）: 取締役会構成・リスク管理・コンプライアンス

## 出力フォーマット
### ESGハイライト（KPI一覧表）
### E（環境）セクション
### S（社会）セクション
### G（ガバナンス）セクション
### 目標と進捗
### 第三者意見への示唆''',
    '報告基準: {{#' + nid(128,1) + '.reporting_standard#}}\n対象年度: {{#' + nid(128,1) + '.fiscal_year#}}\n\nESGデータ:\n{{#' + nid(128,1) + '.esg_data#}}',
    'ESGレポートドラフト')

build('cross-functional', 129, 'dashboard-narrative', '経営ダッシュボードナラティブ', '📊', '#E3F2FD',
    'KPIデータから経営層向けの「数字が語るストーリー」ナラティブレポートを生成する。',
    [V('kpi_data','paragraph'), V('report_period','select',True,['月次','四半期','年次']),
     V('audience','select',True,['経営会議','取締役会','全社'])],
    'kpi_data',
    '''あなたは経営分析の専門家です。KPIデータを「数字が語るストーリー」として経営層に伝わるナラティブレポートに変換してください。

## ルール
1. 数字の羅列ではなく、ストーリーとして読める文章にする
2. 前期比・目標比の増減を明確に示す
3. 良いニュースと悪いニュースをバランスよく伝える
4. 原因分析と対策提案を含める

## 出力フォーマット
### エグゼクティブサマリー（3行以内）
### KPIダッシュボード（表形式）
### ナラティブ分析（ストーリー形式）
### 注目ポイント・リスク
### 推奨アクション''',
    'レポート期間: {{#' + nid(129,1) + '.report_period#}}\n対象: {{#' + nid(129,1) + '.audience#}}\n\nKPIデータ:\n{{#' + nid(129,1) + '.kpi_data#}}',
    '経営ナラティブレポート')

build('cross-functional', 130, 'policy-revision', '社内規程AI検索・改訂ドラフト', '📜', '#FFF3E0',
    '現行規程と法改正情報を照合し改訂ドラフトと改訂理由を生成する。',
    [V('current_policy','paragraph'), V('revision_reason','paragraph'), V('applicable_law','text-input')],
    'current_policy',
    '''あなたは企業法務・コンプライアンスの専門家です。社内規程の改訂ドラフトを作成してください。

## タスク
1. 現行規程の構造を分析し、改訂が必要な条項を特定
2. 法改正や改訂理由に基づく具体的な修正案を作成
3. 新旧対照表を作成

## 出力フォーマット
### 改訂概要サマリー
### 新旧対照表
| 条項 | 現行 | 改訂案 | 改訂理由 |
### 改訂後の規程全文（ドラフト）
### 施行に向けた注意事項''',
    '関連法令: {{#' + nid(130,1) + '.applicable_law#}}\n\n改訂理由:\n{{#' + nid(130,1) + '.revision_reason#}}\n\n現行規程:\n{{#' + nid(130,1) + '.current_policy#}}',
    '規程改訂ドラフト')

# ═══ AUTOMOTIVE (131-138) ═══
print("=== Automotive ===")

AUTO = [
    (131,'drbfm-analysis','品質不具合分析レポート(DRBFM)','🔍','#FFEBEE',
     'DRBFM形式の変化点分析・心配点・対策レポートを自動生成する。',
     [V('defect_info','paragraph'),V('change_point','text-input'),V('affected_model','text-input')],
     'defect_info',
     '変化点: {{#ID.change_point#}}\n対象車種: {{#ID.affected_model#}}\n\n不具合情報:\n{{#ID.defect_info#}}',
     'DRBFMの専門家として、変化点→心配点→対策を構造化してください。\n## 出力\n### 変化点一覧\n### 心配点分析\n### 対策案（設計/工程/検査）\n### 横展開チェックリスト'),
    (132,'recall-analysis','リコール影響範囲分析','🚗','#E3F2FD',
     'リコール情報から影響範囲・対応優先度・顧客通知文を生成する。',
     [V('recall_info','paragraph'),V('affected_vehicles','text-input'),V('production_lot','text-input')],
     'recall_info',
     '対象車両: {{#ID.affected_vehicles#}}\n生産ロット: {{#ID.production_lot#}}\n\nリコール情報:\n{{#ID.recall_info#}}',
     'リコール管理の専門家として分析してください。\n## 出力\n### 影響範囲分析\n### 対応優先度マトリクス\n### 顧客通知文（テンプレート）\n### 対応スケジュール案'),
    (133,'fmea-analysis','FMEA分析シート生成','⚙️','#F3E5F5',
     '故障モード・影響度・検出方法・RPN算出のFMEAシートを生成する。',
     [V('process_info','paragraph'),V('analysis_type','select',True,['設計FMEA','工程FMEA'])],
     'process_info',
     '分析タイプ: {{#ID.analysis_type#}}\n\n工程/設計情報:\n{{#ID.process_info#}}',
     'FMEA分析の専門家として以下を出力してください。\n## 出力\n### FMEAシート\n| 機能 | 故障モード | 影響 | 重大度(S) | 原因 | 発生度(O) | 検出方法 | 検出度(D) | RPN | 推奨対策 |\n### RPN上位5項目の詳細分析\n### 推奨改善策'),
    (134,'dealer-talk-script','ディーラー接客トークスクリプト','🗣️','#E8F5E9',
     '車種情報・顧客属性に基づく接客トークスクリプトを生成する。',
     [V('vehicle_model','text-input'),V('customer_profile','paragraph'),
      V('sales_stage','select',True,['来店初回','試乗後','見積提示','クロージング'])],
     'customer_profile',
     '車種: {{#ID.vehicle_model#}}\n商談ステージ: {{#ID.sales_stage#}}\n\n顧客情報:\n{{#ID.customer_profile#}}',
     '自動車販売の接客スペシャリストとしてトークスクリプトを作成してください。\n## 出力\n### オープニングトーク\n### 車両説明ポイント\n### 想定Q&A（5つ）\n### クロージングトーク\n### 次回アクション誘導'),
    (135,'vehicle-inspection','車両点検レポート生成','🔧','#FFF3E0',
     '点検データから顧客向けレポートと整備提案を自動作成する。',
     [V('inspection_data','paragraph'),V('vehicle_info','text-input'),V('mileage','text-input')],
     'inspection_data',
     '車両: {{#ID.vehicle_info#}}\n走行距離: {{#ID.mileage#}}\n\n点検データ:\n{{#ID.inspection_data#}}',
     '自動車整備の専門家として顧客向けレポートを作成してください。\n## 出力\n### 点検結果サマリー\n| 部位 | 状態 | 判定 | 備考 |\n### 要整備項目（緊急度順）\n### 推奨メンテナンス\n### 次回点検時期の案内'),
    (136,'auto-insurance-quote','自動車保険見積説明書','🛡️','#E8EAF6',
     '車両・顧客情報から保険見積の比較説明書を自動生成する。',
     [V('vehicle_info','paragraph'),V('customer_info','paragraph'),
      V('coverage_type','select',True,['対人対物','車両保険付','フル補償'])],
     'vehicle_info',
     '補償タイプ: {{#ID.coverage_type#}}\n\n車両情報:\n{{#ID.vehicle_info#}}\n\n顧客情報:\n{{#ID.customer_info#}}',
     '自動車保険の専門家として見積説明書を作成してください。\n## 出力\n### 補償内容比較表\n### おすすめプラン\n### 特約オプション解説\n### 保険料の考え方\n### FAQ'),
    (137,'service-campaign','サービスキャンペーン通知文','📢','#FCE4EC',
     'チャネル別のキャンペーン通知文を一括生成する。',
     [V('campaign_info','paragraph'),V('target_vehicles','text-input'),
      V('channel','select',True,['DM','メール','SMS','全チャネル'])],
     'campaign_info',
     '対象車種: {{#ID.target_vehicles#}}\nチャネル: {{#ID.channel#}}\n\nキャンペーン情報:\n{{#ID.campaign_info#}}',
     '自動車ディーラーのマーケティング担当として通知文を作成してください。\n## 出力\n### DM用文面\n### メール用文面（件名＋本文）\n### SMS用文面（70文字以内）\n### 共通CTA・期限表記'),
    (138,'iatf-audit','IATF16949内部監査チェックリスト','✅','#E0F7FA',
     'IATF16949要求事項に基づく監査チェックリストを生成する。',
     [V('audit_scope','paragraph'),V('target_process','select',True,['設計開発','購買','製造','検査','出荷'])],
     'audit_scope',
     '対象プロセス: {{#ID.target_process#}}\n\n監査範囲:\n{{#ID.audit_scope#}}',
     'IATF16949内部監査の専門家としてチェックリストを作成してください。\n## 出力\n### 監査チェックリスト\n| # | 要求事項 | 確認項目 | 適合/不適合 | エビデンス |\n### 重点確認ポイント\n### 前回指摘事項フォロー用チェック'),
]

for num,slug,name,icon,bg,desc,vars_,main_var,usr_tmpl,sys_p in AUTO:
    usr = usr_tmpl.replace('ID', nid(num,1))
    build('automotive',num,slug,name,icon,bg,desc,vars_,main_var,sys_p,usr,name)

# ═══ PHARMA (139-146) ═══
print("=== Pharma ===")

PHARMA = [
    (139,'clinical-protocol-summary','治験プロトコル要約生成','🧪','#E8EAF6',
     '治験計画書からIRB向けPICOT形式の構造化要約を自動作成する。',
     [V('protocol_text','paragraph'),V('study_phase','select',True,['Phase I','Phase II','Phase III','Phase IV'])],
     'protocol_text',
     '治験Phase: {{#ID.study_phase#}}\n\n治験計画書:\n{{#ID.protocol_text#}}',
     '臨床開発の専門家として治験プロトコル要約を作成してください。\n## 出力（PICOT形式）\n### P (Population): 対象患者\n### I (Intervention): 介入\n### C (Comparison): 比較対照\n### O (Outcome): 主要・副次評価項目\n### T (Time): 試験期間\n### 試験デザイン概要\n### 安全性モニタリング計画\n### 倫理的配慮'),
    (140,'package-insert','添付文書ドラフト生成','💊','#FCE4EC',
     '薬理情報から医薬品添付文書のドラフトを自動生成する。',
     [V('drug_info','paragraph'),V('pharmacology_data','paragraph')],
     'drug_info',
     '薬理データ:\n{{#ID.pharmacology_data#}}\n\n薬剤情報:\n{{#ID.drug_info#}}',
     '薬事の専門家として添付文書ドラフトを作成してください。PMDA規定の構成に従い以下を出力:\n### 警告\n### 禁忌\n### 組成・性状\n### 効能又は効果\n### 用法及び用量\n### 重要な基本的注意\n### 相互作用\n### 副作用\n### 薬物動態\n### 臨床成績'),
    (141,'cioms-report','副作用報告(CIOMS)ドラフト','⚠️','#FFF3E0',
     'CIOMS-I形式の個別症例安全性報告書ドラフトを作成する。',
     [V('adverse_event','paragraph'),V('patient_info','paragraph'),V('drug_name','text-input')],
     'adverse_event',
     '薬剤名: {{#ID.drug_name#}}\n\n患者情報:\n{{#ID.patient_info#}}\n\n有害事象:\n{{#ID.adverse_event#}}',
     'ファーマコビジランスの専門家としてCIOMS-I報告書ドラフトを作成してください。\n## 出力\n### 患者情報（年齢/性別/体重）\n### 有害事象の概要\n### 被疑薬情報\n### 経過\n### 因果関係評価\n### 報告者評価\n### MedDRAコーディング案'),
    (142,'mr-detailing','MRディテーリング資料生成','👨\u200d⚕️','#E8F5E9',
     'MR用ディテーリング資料を生成する。',
     [V('product_info','paragraph'),V('competitor_info','paragraph'),
      V('target_specialty','select',True,['内科','外科','小児科','精神科','その他'])],
     'product_info',
     '対象診療科: {{#ID.target_specialty#}}\n\n競合情報:\n{{#ID.competitor_info#}}\n\n製品情報:\n{{#ID.product_info#}}',
     'MRの専門家としてディテーリング資料を作成してください。\n## 出力\n### 製品プロファイル\n### キーメッセージ（3つ）\n### 競合比較表\n### 想定Q&A（5つ）\n### クリニカルエビデンス要約\n### ディテーリングフロー（話法）'),
    (143,'gmp-deviation','GMP逸脱報告書生成','🏭','#E3F2FD',
     'GMP逸脱報告書（CAPA付き）を自動作成する。',
     [V('deviation_info','paragraph'),V('impact_assessment','paragraph'),V('product_name','text-input')],
     'deviation_info',
     '製品名: {{#ID.product_name#}}\n\n影響評価:\n{{#ID.impact_assessment#}}\n\n逸脱情報:\n{{#ID.deviation_info#}}',
     'GMP品質保証の専門家として逸脱報告書を作成してください。\n## 出力\n### 逸脱概要\n### 影響評価（品質/安全性/有効性）\n### 根本原因分析（なぜなぜ分析）\n### CAPA（是正・予防措置）\n| 区分 | 対策内容 | 担当 | 期限 | 確認方法 |\n### 水平展開チェック'),
    (144,'stability-test','安定性試験レポート','🌡️','#FFF8E1',
     'ICH Q1準拠の安定性試験レポートを生成する。',
     [V('test_data','paragraph'),V('storage_conditions','select',True,['長期保存','加速試験','苛酷試験']),
      V('drug_name','text-input')],
     'test_data',
     '薬剤名: {{#ID.drug_name#}}\n試験条件: {{#ID.storage_conditions#}}\n\n試験データ:\n{{#ID.test_data#}}',
     'ICH Q1ガイドラインに基づき安定性試験レポートを作成してください。\n## 出力\n### 試験条件・検体情報\n### 試験結果一覧\n| 試験項目 | 初期値 | 3M | 6M | 9M | 12M | 規格 | 判定 |\n### トレンド分析\n### 有効期間の設定根拠\n### 結論'),
    (145,'ctd-summary','薬事申請CTD要約','📑','#E8EAF6',
     'CTDモジュール概要ドラフトを自動生成する。',
     [V('ctd_data','paragraph'),V('module','select',True,['品質(Module3)','非臨床(Module4)','臨床(Module5)'])],
     'ctd_data',
     'モジュール: {{#ID.module#}}\n\nCTDデータ:\n{{#ID.ctd_data#}}',
     '薬事申請の専門家としてCTD概要ドラフトを作成してください。指定モジュールの概要を構造化して出力します。\n## 出力\n### モジュール概要\n### 主要データのサマリー\n### 品質/安全性/有効性の総合評価\n### 規制上の論点\n### 参考文献リスト'),
    (146,'pv-signal-analysis','PVシグナル分析レポート','📈','#E0F2F1',
     'シグナル検出・評価・対応推奨の分析レポートを生成する。',
     [V('adverse_event_data','paragraph'),V('analysis_period','select',True,['月次','四半期','年次']),
      V('drug_name','text-input')],
     'adverse_event_data',
     '薬剤名: {{#ID.drug_name#}}\n分析期間: {{#ID.analysis_period#}}\n\n有害事象データ:\n{{#ID.adverse_event_data#}}',
     'ファーマコビジランスの専門家としてシグナル分析レポートを作成してください。\n## 出力\n### シグナル検出結果\n| シグナル | PRR | ROR | 評価 |\n### 既知/新規シグナルの分類\n### リスク評価\n### 対応推奨（追加調査/添付文書改訂/当局報告等）\n### ベネフィット-リスク評価'),
]

for num,slug,name,icon,bg,desc,vars_,main_var,usr_tmpl,sys_p in PHARMA:
    usr = usr_tmpl.replace('ID', nid(num,1))
    build('pharma',num,slug,name,icon,bg,desc,vars_,main_var,sys_p,usr,name)

# ═══ ENERGY (147-154) ═══
print("=== Energy ===")

ENERGY = [
    (147,'plant-inspection','プラント巡視点検レポート','🏗️','#E3F2FD',
     '異常検知ハイライト付き点検レポートを自動作成する。',
     [V('inspection_data','paragraph'),V('plant_type','select',True,['火力発電','水力発電','変電所','ガスプラント']),
      V('inspection_date','text-input')],
     'inspection_data',
     'プラント種別: {{#ID.plant_type#}}\n点検日: {{#ID.inspection_date#}}\n\n点検データ:\n{{#ID.inspection_data#}}',
     'プラント保全の専門家として点検レポートを作成してください。\n## 出力\n### 点検サマリー\n### 異常検知ハイライト（赤/黄/緑）\n| 設備 | 測定値 | 基準値 | 判定 | 対応 |\n### 要対応事項（緊急度順）\n### 次回点検時の重点確認項目'),
    (148,'power-demand-forecast','電力需給予測ナラティブ','⚡','#FFF8E1',
     '需給データと気象予報から需給予測説明レポートを自動生成する。',
     [V('demand_data','paragraph'),V('weather_forecast','paragraph'),V('region','text-input')],
     'demand_data',
     '地域: {{#ID.region#}}\n\n気象予報:\n{{#ID.weather_forecast#}}\n\n需給データ:\n{{#ID.demand_data#}}',
     '電力需給運用の専門家として予測ナラティブを作成してください。\n## 出力\n### 需給予測サマリー\n### 需要側要因分析（気温/曜日/イベント）\n### 供給側状況\n### リスクシナリオ\n### 運用推奨アクション'),
    (149,'environmental-assessment','環境アセスメント報告書','🌿','#E8F5E9',
     '環境影響評価報告書のドラフトを生成する。',
     [V('survey_data','paragraph'),V('project_type','select',True,['建設','工場','再エネ','インフラ']),
      V('location','text-input')],
     'survey_data',
     'プロジェクト種別: {{#ID.project_type#}}\n所在地: {{#ID.location#}}\n\n調査データ:\n{{#ID.survey_data#}}',
     '環境アセスメントの専門家として報告書ドラフトを作成してください。\n## 出力\n### 事業概要\n### 環境影響評価\n| 項目 | 現況 | 予測影響 | 低減措置 |\n### 大気/水質/騒音/振動/生態系\n### 総合評価\n### モニタリング計画'),
    (150,'equipment-rca','設備故障RCAレポート','🔩','#FFEBEE',
     '根本原因分析と再発防止策レポートを自動作成する。',
     [V('failure_info','paragraph'),V('equipment_id','text-input'),V('operation_history','paragraph')],
     'failure_info',
     '設備ID: {{#ID.equipment_id#}}\n\n運転履歴:\n{{#ID.operation_history#}}\n\n故障情報:\n{{#ID.failure_info#}}',
     '設備保全の専門家としてRCAレポートを作成してください。\n## 出力\n### 故障概要\n### 時系列分析\n### 根本原因分析（FTA/なぜなぜ）\n### 再発防止策\n| 対策 | 担当 | 期限 | 効果確認方法 |\n### 水平展開チェック'),
    (151,'carbon-footprint','カーボンフットプリント計算書','🌍','#E0F7FA',
     'CO2排出量計算書（スコープ別）を自動生成する。',
     [V('emission_data','paragraph'),V('scope','select',True,['Scope1','Scope2','Scope3','全スコープ']),
      V('fiscal_year','text-input')],
     'emission_data',
     '対象スコープ: {{#ID.scope#}}\n対象年度: {{#ID.fiscal_year#}}\n\n排出データ:\n{{#ID.emission_data#}}',
     'カーボンニュートラルの専門家としてCO2排出量計算書を作成してください。\n## 出力\n### 排出量サマリー\n| スコープ | カテゴリ | 排出量(tCO2) | 前年比 |\n### 算定方法・排出係数\n### 削減目標との比較\n### 削減施策の提案\n### SBT整合性チェック'),
    (152,'safety-regulation','保安規程チェックリスト','📋','#FFF3E0',
     '法令に基づく保安規程チェックリストを生成する。',
     [V('facility_info','paragraph'),V('applicable_law','select',True,['電気事業法','ガス事業法','高圧ガス保安法','消防法'])],
     'facility_info',
     '適用法令: {{#ID.applicable_law#}}\n\n施設情報:\n{{#ID.facility_info#}}',
     '保安管理の専門家としてチェックリストを作成してください。\n## 出力\n### 適用条項一覧\n### チェックリスト\n| # | 確認項目 | 根拠条文 | 適合/不適合 | エビデンス |\n### 重点確認事項\n### 改善が必要な場合の対応手順'),
    (153,'power-pricing','電力料金プラン提案書','💡','#E8F5E9',
     '最適料金プラン比較と提案書を自動作成する。',
     [V('usage_data','paragraph'),V('current_contract','text-input'),
      V('customer_type','select',True,['低圧','高圧','特別高圧'])],
     'usage_data',
     '契約種別: {{#ID.customer_type#}}\n現行契約: {{#ID.current_contract#}}\n\n使用電力データ:\n{{#ID.usage_data#}}',
     '電力小売の営業担当として料金プラン提案書を作成してください。\n## 出力\n### 現行契約分析\n### プラン比較表\n| プラン | 基本料金 | 従量単価 | 年間概算 | 削減額 |\n### おすすめプラン\n### 切替メリット・注意事項'),
    (154,'renewable-monthly','再エネ発電所月次報告','☀️','#FFF8E1',
     '月次運転報告書を自動生成する。',
     [V('generation_data','paragraph'),V('plant_type','select',True,['太陽光','風力','バイオマス','小水力']),
      V('month','text-input')],
     'generation_data',
     '発電種別: {{#ID.plant_type#}}\n対象月: {{#ID.month#}}\n\n発電データ:\n{{#ID.generation_data#}}',
     '再エネ発電所の運転管理専門家として月次報告書を作成してください。\n## 出力\n### 発電実績サマリー\n| 項目 | 実績 | 計画 | 達成率 |\n### 設備利用率分析\n### 気象条件との相関\n### 保守・トラブル報告\n### 翌月の見通し'),
]

for num,slug,name,icon,bg,desc,vars_,main_var,usr_tmpl,sys_p in ENERGY:
    usr = usr_tmpl.replace('ID', nid(num,1))
    build('energy',num,slug,name,icon,bg,desc,vars_,main_var,sys_p,usr,name)

# ═══ TRAVEL (155-162) ═══
print("=== Travel ===")

TRAVEL = [
    (155,'travel-plan','旅行プラン自動提案','✈️','#E3F2FD',
     'パーソナライズされた旅行プラン＋概算見積を自動生成する。',
     [V('preferences','paragraph'),V('budget','text-input'),
      V('duration','select',True,['日帰り','1泊2日','2泊3日','3泊以上']),
      V('travelers','select',True,['1人','カップル','家族','グループ'])],
     'preferences',
     '予算: {{#ID.budget#}}\n日程: {{#ID.duration#}}\n人数: {{#ID.travelers#}}\n\n希望条件:\n{{#ID.preferences#}}',
     '旅行プランナーとして最適な旅行プランを提案してください。\n## 出力\n### おすすめプラン（2案）\n### 日程表（時間帯別）\n### 宿泊施設候補\n### 概算見積\n### 予約時の注意事項'),
    (156,'multilingual-guide','観光地多言語ガイド生成','🗺️','#E8F5E9',
     '日本語＋指定言語の多言語ガイド文を一括生成する。',
     [V('spot_info','paragraph'),V('target_languages','select',True,['英語','中国語(簡体)','中国語(繁体)','韓国語'])],
     'spot_info',
     '対象言語: {{#ID.target_languages#}}\n\n観光スポット情報:\n{{#ID.spot_info#}}',
     '観光ガイドの翻訳専門家として多言語ガイド文を作成してください。\n## 出力\n### 日本語ガイド文\n### 英語ガイド文\n### 指定言語ガイド文\n### 文化的補足（各言語圏の観光客向け）\n### 音声ガイド用スクリプト'),
    (157,'ota-review-analysis','OTA口コミ分析・改善提案','⭐','#FFF3E0',
     '口コミデータから評価分析・改善優先度・回答文を自動生成する。',
     [V('reviews','paragraph'),V('facility_type','select',True,['ホテル','旅館','ゲストハウス','リゾート'])],
     'reviews',
     '施設タイプ: {{#ID.facility_type#}}\n\n口コミデータ:\n{{#ID.reviews#}}',
     '宿泊施設のCX専門家として口コミ分析を行ってください。\n## 出力\n### 評価サマリー（カテゴリ別平均）\n### ポジティブ/ネガティブ キーワード\n### 改善優先度マトリクス\n### 口コミ回答文テンプレート（好評/不満別）\n### 競合との差別化ポイント'),
    (158,'accommodation-plan','宿泊プラン企画書','🏨','#F3E5F5',
     '宿泊プラン企画書（料金設計・販促文含む）を作成する。',
     [V('facility_info','paragraph'),V('target_segment','select',True,['ビジネス','カップル','ファミリー','インバウンド']),
      V('season','select',True,['春','夏','秋','冬','通年'])],
     'facility_info',
     'ターゲット: {{#ID.target_segment#}}\nシーズン: {{#ID.season#}}\n\n施設情報:\n{{#ID.facility_info#}}',
     '宿泊施設の企画担当として魅力的なプランを企画してください。\n## 出力\n### プラン名・コンセプト\n### プラン内容（含まれるもの）\n### 料金設計\n### OTA掲載用説明文\n### 販促施策案'),
    (159,'inbound-phrases','インバウンド接客フレーズ集','💬','#E0F7FA',
     '英中韓の接客フレーズと対応マニュアルを自動生成する。',
     [V('business_type','select',True,['ホテル','飲食店','小売店','観光施設']),
      V('common_scenarios','paragraph')],
     'common_scenarios',
     '業態: {{#ID.business_type#}}\n\nよくあるシーン:\n{{#ID.common_scenarios#}}',
     'インバウンド接客の専門家として多言語フレーズ集を作成してください。\n## 出力\n### シーン別フレーズ一覧\n| シーン | 日本語 | English | 中文 | 한국어 |\n### 発音ガイド（カタカナ読み）\n### トラブル対応フレーズ\n### 文化的注意事項'),
    (160,'tour-guide-script','ツアーガイド台本生成','🎤','#FFF8E1',
     'ガイドトークスクリプト（歴史・豆知識含む）を作成する。',
     [V('route_info','paragraph'),V('duration','text-input'),
      V('theme','select',True,['歴史文化','自然','グルメ','アドベンチャー'])],
     'route_info',
     '所要時間: {{#ID.duration#}}\nテーマ: {{#ID.theme#}}\n\nルート情報:\n{{#ID.route_info#}}',
     'プロのツアーガイドとして台本を作成してください。\n## 出力\n### オープニングトーク\n### スポット別ガイド（各スポットの説明・豆知識・フォトスポット案内）\n### 移動中のトーク（歴史/文化エピソード）\n### クロージングトーク\n### 想定Q&A'),
    (161,'travel-regulation','旅行業約款チェックリスト','📝','#FFEBEE',
     '旅行業法に基づく説明事項チェックリストを生成する。',
     [V('tour_details','paragraph'),V('tour_type','select',True,['募集型企画旅行','受注型企画旅行','手配旅行'])],
     'tour_details',
     '旅行種別: {{#ID.tour_type#}}\n\nツアー内容:\n{{#ID.tour_details#}}',
     '旅行業法の専門家としてチェックリストを作成してください。\n## 出力\n### 重要事項説明チェックリスト\n| # | 説明項目 | 根拠条文 | 確認 |\n### 取消料規定\n### 特別補償規程の確認\n### 旅程保証の確認'),
    (162,'tourism-marketing','観光マーケティングレポート','📊','#E8EAF6',
     '観光DMP分析レポートを自動生成する。',
     [V('tourism_data','paragraph'),V('region','text-input'),V('analysis_period','select',True,['月次','四半期','年次'])],
     'tourism_data',
     '地域: {{#ID.region#}}\n分析期間: {{#ID.analysis_period#}}\n\n観光データ:\n{{#ID.tourism_data#}}',
     '観光マーケティングの専門家として分析レポートを作成してください。\n## 出力\n### 来訪者数推移\n### 属性分析（国籍/年代/目的）\n### 消費額分析\n### 満足度・リピート意向\n### 施策効果検証\n### 次期施策提案'),
]

for num,slug,name,icon,bg,desc,vars_,main_var,usr_tmpl,sys_p in TRAVEL:
    usr = usr_tmpl.replace('ID', nid(num,1))
    build('travel',num,slug,name,icon,bg,desc,vars_,main_var,sys_p,usr,name)

# ═══ AGRICULTURE (163-170) ═══
print("=== Agriculture ===")

AGRI = [
    (163,'cultivation-record','栽培記録・出荷記録生成','🌾','#E8F5E9',
     'GAP準拠の栽培記録と出荷記録を自動作成する。',
     [V('crop_info','paragraph'),V('pesticide_records','paragraph'),V('harvest_data','text-input')],
     'crop_info',
     '収穫データ: {{#ID.harvest_data#}}\n\n農薬使用記録:\n{{#ID.pesticide_records#}}\n\n作物情報:\n{{#ID.crop_info#}}',
     'GAP認証の専門家として栽培記録を作成してください。\n## 出力\n### 栽培記録（圃場別）\n| 日付 | 作業内容 | 使用資材 | 作業者 |\n### 農薬使用記録\n| 日付 | 薬剤名 | 希釈倍率 | 散布面積 | 収穫前日数 |\n### 出荷記録\n### GAP適合チェック'),
    (164,'haccp-record','HACCP管理記録シート','🔬','#E3F2FD',
     'HACCP義務化対応の管理記録シートを自動生成する。',
     [V('process_info','paragraph'),V('ccp_info','paragraph'),
      V('product_type','select',True,['加工食品','飲料','乳製品','水産加工'])],
     'process_info',
     '製品種別: {{#ID.product_type#}}\n\nCCP情報:\n{{#ID.ccp_info#}}\n\n工程情報:\n{{#ID.process_info#}}',
     'HACCP管理の専門家として管理記録シートを作成してください。\n## 出力\n### 工程フロー図\n### ハザード分析表\n| 工程 | ハザード | 管理手段 | CCP判定 |\n### CCP管理記録シート\n| CCP | 管理基準 | モニタリング方法 | 是正措置 |\n### 一般衛生管理記録'),
    (165,'farm-product-description','農産物POP・商品説明文','🍎','#FFF3E0',
     '直売所向けPOPとEC用商品説明を自動生成する。',
     [V('product_info','paragraph'),V('producer_info','text-input'),
      V('sales_channel','select',True,['直売所','EC','スーパー','レストラン'])],
     'product_info',
     '生産者: {{#ID.producer_info#}}\n販売チャネル: {{#ID.sales_channel#}}\n\n商品情報:\n{{#ID.product_info#}}',
     '農産物マーケティングの専門家として販促文を作成してください。\n## 出力\n### 直売所POP文（50文字以内のキャッチコピー + 説明）\n### EC用商品説明文（SEO対応）\n### 生産者ストーリー\n### おすすめレシピ（2品）\n### SNS投稿文案'),
    (166,'food-label-check','食品表示ラベルチェック','🏷️','#FFEBEE',
     '食品表示法準拠のラベル表記チェック結果を生成する。',
     [V('ingredients','paragraph'),V('allergens','paragraph'),V('product_name','text-input')],
     'ingredients',
     '商品名: {{#ID.product_name#}}\n\nアレルゲン情報:\n{{#ID.allergens#}}\n\n原材料:\n{{#ID.ingredients#}}',
     '食品表示法の専門家としてラベルチェックを行ってください。\n## 出力\n### 表示ラベル案\n### チェック結果\n| チェック項目 | 適合/不適合 | 指摘事項 |\n### アレルゲン表示確認\n### 栄養成分表示案\n### 改善が必要な点'),
    (167,'agri-subsidy','農水省補助金申請ドラフト','💰','#E8EAF6',
     '農水省系補助金の申請書ドラフトを自動作成する。',
     [V('business_plan','paragraph'),V('subsidy_program','select',True,['経営体育成','スマート農業','6次産業化','環境保全型']),
      V('applicant_info','text-input')],
     'business_plan',
     '補助金プログラム: {{#ID.subsidy_program#}}\n申請者: {{#ID.applicant_info#}}\n\n事業計画:\n{{#ID.business_plan#}}',
     '農業補助金申請の専門家としてドラフトを作成してください。\n## 出力\n### 事業概要\n### 事業の目的・必要性\n### 事業内容・実施計画\n### 事業費積算\n| 経費区分 | 内容 | 金額 |\n### 期待される成果（KPI）\n### 事業実施体制'),
    (168,'pest-diagnosis','病害虫診断・対策提案','🐛','#F1F8E9',
     '病害虫の推定診断と防除対策を提案する。',
     [V('symptoms','paragraph'),V('crop_type','text-input'),V('growing_conditions','paragraph')],
     'symptoms',
     '作物: {{#ID.crop_type#}}\n\n栽培条件:\n{{#ID.growing_conditions#}}\n\n症状:\n{{#ID.symptoms#}}',
     '植物病理・害虫学の専門家として診断と対策を提案してください。\n## 出力\n### 推定診断（可能性の高い順）\n| 候補 | 可能性 | 根拠 |\n### 詳細説明（発生条件・伝染経路）\n### 防除対策\n- 耕種的対策\n- 生物的対策\n- 化学的対策（農薬名・使用方法）\n### 予防措置\n※最終判断は農業普及指導員にご相談ください。'),
    (169,'traceability-report','トレーサビリティ報告書','🔗','#E0F2F1',
     '食品トレーサビリティ報告書を自動生成する。',
     [V('production_data','paragraph'),V('distribution_data','paragraph'),V('product_name','text-input')],
     'production_data',
     '商品名: {{#ID.product_name#}}\n\n流通データ:\n{{#ID.distribution_data#}}\n\n生産データ:\n{{#ID.production_data#}}',
     'トレーサビリティの専門家として報告書を作成してください。\n## 出力\n### 製品識別情報\n### 原材料トレース\n| 原材料 | 産地 | 仕入先 | ロット |\n### 製造工程トレース\n### 流通経路トレース\n### 品質管理記録サマリー'),
    (170,'sixth-industry-plan','6次産業化事業計画書','🌿','#FFF8E1',
     '6次産業化の事業計画書ドラフトを自動作成する。',
     [V('farm_products','paragraph'),V('processing_idea','paragraph'),V('sales_channels','paragraph')],
     'farm_products',
     '販路:\n{{#ID.sales_channels#}}\n\n加工アイデア:\n{{#ID.processing_idea#}}\n\n農産物:\n{{#ID.farm_products#}}',
     '6次産業化の専門家として事業計画書を作成してください。\n## 出力\n### 事業コンセプト\n### 1次（生産）計画\n### 2次（加工）計画\n### 3次（販売）計画\n### 収支計画（3年）\n| 項目 | 1年目 | 2年目 | 3年目 |\n### リスク分析と対策\n### 必要な許認可一覧'),
]

for num,slug,name,icon,bg,desc,vars_,main_var,usr_tmpl,sys_p in AGRI:
    usr = usr_tmpl.replace('ID', nid(num,1))
    build('agriculture',num,slug,name,icon,bg,desc,vars_,main_var,sys_p,usr,name)

# ═══ SUMMARY ═══
print("\n=== Generation Complete ===")
import glob
total = len(glob.glob(os.path.join(BASE, '**', 'ais-*.yml'), recursive=True))
print(f"Total YAML files generated: {total}")
for cat in ['cross-functional','automotive','pharma','energy','travel','agriculture']:
    count = len(glob.glob(os.path.join(BASE, cat, 'ais-*.yml')))
    print(f"  {cat}: {count} files")
