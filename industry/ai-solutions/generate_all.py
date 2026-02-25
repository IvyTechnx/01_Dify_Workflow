#!/usr/bin/env python3
"""
AI Solutions ファミレスメニュー: 新規15ワークフロー一括生成スクリプト
既存 AIS-01〜10 に加え、AIS-11〜25 を生成する
"""

import yaml
import os
import textwrap

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 共通テンプレート部品
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SENSITIVE_WORDS_CONFIG = {
    "enabled": True,
    "type": "keywords",
    "config": {
        "keywords": "爆弾\n殺害\n違法薬物\nハッキング手法",
        "inputs_config": {
            "enabled": True,
            "preset_response": "その内容にはお答えできません。別の質問をお願いします。"
        },
        "outputs_config": {
            "enabled": True,
            "preset_response": "適切な回答を生成できませんでした。質問を変えてください。"
        }
    }
}

BASE_FEATURES = {
    "file_upload": {
        "image": {
            "enabled": False,
            "number_limits": 3,
            "transfer_methods": ["local_file", "remote_url"]
        }
    },
    "opening_statement": "",
    "retriever_resource": {"enabled": False},
    "sensitive_word_avoidance": SENSITIVE_WORDS_CONFIG,
    "speech_to_text": {"enabled": False},
    "suggested_questions": [],
    "suggested_questions_after_answer": {"enabled": False},
    "text_to_speech": {"enabled": False, "language": "", "voice": ""}
}

INJECTION_CODE = '''import re

def main({params}) -> dict:
    issues = []
{checks}
    # プロンプトインジェクション検査
    injection_patterns = [
        r'(?i)ignore\\s+(previous|above|all)\\s+(instructions?|prompts?)',
        r'(?i)system\\s*prompt',
        r'(?i)you\\s+are\\s+now',
        r'(?i)forget\\s+(everything|all|your)',
        r'<script',
        r'javascript:',
        r'\\{{\\{{.*\\}}\\}}',
    ]
    combined = {combined_var}
    for pattern in injection_patterns:
        if re.search(pattern, combined):
            issues.append("不正な入力パターンが検出されました。正しい内容を入力してください。")
            break

    is_valid = "true" if len(issues) == 0 else "false"
    error_message = "" if is_valid == "true" else "\\n".join(issues)
    return {{'is_valid': is_valid, 'error_message': error_message}}'''


def make_node_id(ais_num, node_num):
    """AIS番号とノード番号からID生成: AIS-11 node 1 → 51100000000001"""
    return str(ais_num * 100000000000 + 50000000000000 + node_num)


def make_edge_id(ais_num, src, tgt):
    return f"e-{make_node_id(ais_num, src)}-{make_node_id(ais_num, tgt)}"


def node_base(ais_num, node_num, x, y, ntype, title, desc, height=97, width=243, extra=None):
    nid = make_node_id(ais_num, node_num)
    n = {
        "data": {
            "desc": desc,
            "selected": False,
            "title": title,
            "type": ntype,
        },
        "height": height,
        "id": nid,
        "position": {"x": x, "y": y},
        "positionAbsolute": {"x": x, "y": y},
        "selected": False,
        "sourcePosition": "right",
        "targetPosition": "left",
        "type": "custom",
        "width": width,
    }
    if extra:
        n["data"].update(extra)
    return n


def edge(ais_num, src_num, tgt_num, src_type, tgt_type, handle="source"):
    return {
        "data": {"sourceType": src_type, "targetType": tgt_type, "isInIteration": False},
        "id": make_edge_id(ais_num, src_num, tgt_num),
        "source": make_node_id(ais_num, src_num),
        "sourceHandle": handle,
        "target": make_node_id(ais_num, tgt_num),
        "targetHandle": "target",
        "type": "custom",
    }


def llm_node(ais_num, node_num, x, y, title, desc, system_prompt, user_prompt, temp=0.3, max_tokens=4096):
    return node_base(ais_num, node_num, x, y, "llm", title, desc, extra={
        "context": {"enabled": False, "variable_selector": []},
        "model": {
            "completion_params": {
                "frequency_penalty": 0, "max_tokens": max_tokens,
                "presence_penalty": 0, "temperature": temp, "top_p": 1
            },
            "mode": "chat", "name": "gpt-4o-mini", "provider": "openai"
        },
        "prompt_template": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt}
        ],
        "variables": [],
        "vision": {"enabled": False}
    })


def code_node(ais_num, node_num, x, y, title, desc, code, variables, outputs):
    return node_base(ais_num, node_num, x, y, "code", title, desc, extra={
        "code_language": "python3",
        "code": code,
        "variables": variables,
        "outputs": outputs
    })


def ifelse_node(ais_num, node_num, x, y, title, desc, var_node, var_name):
    return node_base(ais_num, node_num, x, y, "if-else", title, desc, height=125, extra={
        "cases": [{
            "case_id": "true",
            "logical_operator": "and",
            "conditions": [{
                "id": "condition_valid",
                "variable_selector": [make_node_id(ais_num, var_node), var_name],
                "comparison_operator": "is",
                "value": "true"
            }]
        }]
    })


def tt_node(ais_num, node_num, x, y, title, desc, template, variables):
    return node_base(ais_num, node_num, x, y, "template-transform", title, desc, extra={
        "template": template,
        "variables": variables
    })


def end_node(ais_num, node_num, x, y, outputs):
    return node_base(ais_num, node_num, x, y, "end", "終了",
                     "結果またはエラーメッセージを出力する", height=89, extra={"outputs": outputs})


def error_tt(ais_num, node_num, x, y, title_text, guide_text, error_var_node):
    return tt_node(ais_num, node_num, x, y, "エラー応答",
                   "入力検証エラー時のエラーメッセージを整形する",
                   f"## 入力エラー\n\n{title_text}\n\n**エラー詳細**: {{{{ error_message }}}}\n\n### 入力ガイド\n{guide_text}\n\n入力内容を修正して再度お試しください。",
                   [{"value_selector": [make_node_id(ais_num, error_var_node), "error_message"], "variable": "error_message"}])


def build_workflow(ais_num, app_name, app_desc, icon, icon_bg, mode, nodes, edges_list, features_override=None):
    features = dict(BASE_FEATURES)
    if features_override:
        features.update(features_override)

    doc = {
        "kind": "app",
        "version": "0.1.5",
        "app": {
            "description": app_desc,
            "icon": icon,
            "icon_background": icon_bg,
            "mode": mode,
            "name": app_name,
            "use_icon_as_answer_icon": False,
        },
        "workflow": {
            "environment_variables": [],
            "conversation_variables": [],
            "features": features,
            "graph": {
                "edges": edges_list,
                "nodes": nodes,
                "viewport": {"x": 0, "y": 0, "zoom": 1}
            }
        }
    }
    return doc


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ワークフロー定義 AIS-11〜AIS-25
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_ais_11():
    """AIS-11: メール文面パーソナライズ生成"""
    A = 11
    nodes = [
        node_base(A, 1, 80, 282, "start", "開始", "送信先・目的・コンテキストを受け取る", height=149, extra={
            "variables": [
                {"label": "recipient_info", "max_length": 5000, "options": [], "required": True, "type": "paragraph", "variable": "recipient_info"},
                {"label": "email_purpose", "max_length": 48, "options": ["アポイント依頼", "フォローアップ", "提案送付", "お礼メール", "催促メール", "お詫びメール"], "required": True, "type": "select", "variable": "email_purpose"},
                {"label": "key_points", "max_length": 10000, "options": [], "required": False, "type": "paragraph", "variable": "key_points"},
                {"label": "tone", "max_length": 48, "options": ["丁寧・フォーマル", "ビジネスカジュアル", "親しみやすい"], "required": True, "type": "select", "variable": "tone"},
            ]
        }),
        code_node(A, 2, 380, 282, "入力検証", "送信先情報の長さチェックとインジェクション検出を行う",
            INJECTION_CODE.format(
                params="recipient_info: str",
                checks='    if len(recipient_info.strip()) < 5:\n        issues.append("送信先情報が短すぎます（5文字以上必要）")\n    if len(recipient_info) > 5000:\n        issues.append("送信先情報が長すぎます（5000文字以下にしてください）")',
                combined_var="recipient_info"
            ),
            [{"value_selector": [make_node_id(A, 1), "recipient_info"], "variable": "recipient_info"}],
            {"is_valid": {"type": "string"}, "error_message": {"type": "string"}}
        ),
        ifelse_node(A, 3, 680, 282, "検証結果分岐", "入力検証結果で分岐する", 2, "is_valid"),
        llm_node(A, 4, 980, 182, "メール生成", "パーソナライズされたメール文面を3案生成する",
            "あなたはビジネスメールの専門コピーライターです。送信先の情報と目的に基づいて、パーソナライズされたメール文面を3案生成してください。\n\n## 出力フォーマット\n各案について以下を出力:\n### 案1\n**件名**: （件名）\n**本文**:\n（本文）\n\n## ルール\n- 送信先の業界・役職・状況に合わせた表現を使用する\n- 指定されたトーンを厳守する\n- 目的に沿った明確なCTA（行動喚起）を含める\n- 件名は開封率を意識した魅力的な文言にする\n- 各案は異なるアプローチ（論理的/感情的/具体例ベース等）で作成する\n- 個人情報は出力しない\n- 押し付けがましい表現は避ける",
            "送信先情報: {{#" + make_node_id(A, 1) + ".recipient_info#}}\nメール目的: {{#" + make_node_id(A, 1) + ".email_purpose#}}\nキーポイント: {{#" + make_node_id(A, 1) + ".key_points#}}\nトーン: {{#" + make_node_id(A, 1) + ".tone#}}",
            temp=0.7),
        tt_node(A, 5, 1280, 182, "出力整形", "メール文面にメタ情報を付与して整形する",
            "# メール文面生成結果\n\n**目的**: {{ email_purpose }}\n**トーン**: {{ tone }}\n\n---\n\n{{ email_drafts }}\n\n---\n*AIが生成したメール文面です。送信前に内容を確認・調整してください。*",
            [
                {"value_selector": [make_node_id(A, 4), "text"], "variable": "email_drafts"},
                {"value_selector": [make_node_id(A, 1), "email_purpose"], "variable": "email_purpose"},
                {"value_selector": [make_node_id(A, 1), "tone"], "variable": "tone"},
            ]),
        error_tt(A, 6, 980, 432, "メール文面の生成を開始できませんでした。",
                 "- 送信先情報は5文字以上で入力してください\n- 不正な文字列は使用できません", 2),
        end_node(A, 7, 1580, 282, [
            {"value_selector": [make_node_id(A, 5), "output"], "variable": "email_result"},
            {"value_selector": [make_node_id(A, 6), "output"], "variable": "error_message"},
        ]),
    ]
    edges_list = [
        edge(A, 1, 2, "start", "code"),
        edge(A, 2, 3, "code", "if-else"),
        edge(A, 3, 4, "if-else", "llm", "true"),
        edge(A, 3, 6, "if-else", "template-transform", "false"),
        edge(A, 4, 5, "llm", "template-transform"),
        edge(A, 5, 7, "template-transform", "end"),
        edge(A, 6, 7, "template-transform", "end"),
    ]
    return build_workflow(A, "AIS-11: メール文面パーソナライズ生成", "送信先情報と目的を指定すると、パーソナライズされたビジネスメール文面を3案生成するワークフロー。Lavender/Smartwriterに対抗するAIメールライティング機能。", "\U0001F4E7", "#E3F2FD", "workflow", nodes, edges_list)


def build_ais_12():
    """AIS-12: 競合分析レポート生成"""
    A = 12
    nodes = [
        node_base(A, 1, 80, 282, "start", "開始", "自社情報・競合企業・分析観点を受け取る", height=149, extra={
            "variables": [
                {"label": "own_company_info", "max_length": 10000, "options": [], "required": True, "type": "paragraph", "variable": "own_company_info"},
                {"label": "competitors", "max_length": 10000, "options": [], "required": True, "type": "paragraph", "variable": "competitors"},
                {"label": "analysis_focus", "max_length": 48, "options": ["総合分析", "価格戦略", "機能比較", "マーケティング戦略", "技術力比較"], "required": True, "type": "select", "variable": "analysis_focus"},
                {"label": "industry", "max_length": 256, "options": [], "required": True, "type": "text-input", "variable": "industry"},
            ]
        }),
        code_node(A, 2, 380, 282, "入力検証", "自社情報・競合情報の文字数チェックとインジェクション検出",
            INJECTION_CODE.format(
                params="own_company_info: str, competitors: str",
                checks='    if len(own_company_info.strip()) < 20:\n        issues.append("自社情報が短すぎます（20文字以上必要）")\n    if len(competitors.strip()) < 10:\n        issues.append("競合企業情報が短すぎます（10文字以上必要）")',
                combined_var="own_company_info + ' ' + competitors"
            ),
            [
                {"value_selector": [make_node_id(A, 1), "own_company_info"], "variable": "own_company_info"},
                {"value_selector": [make_node_id(A, 1), "competitors"], "variable": "competitors"},
            ],
            {"is_valid": {"type": "string"}, "error_message": {"type": "string"}}
        ),
        ifelse_node(A, 3, 680, 282, "検証結果分岐", "入力検証結果で分岐する", 2, "is_valid"),
        llm_node(A, 4, 980, 182, "競合分析", "競合企業の強み・弱みを多角的に分析する",
            "あなたは戦略コンサルタントです。自社と競合企業の情報に基づいて、詳細な競合分析レポートを作成してください。\n\n## レポート構成\n1. **エグゼクティブサマリー**（3行以内）\n2. **市場環境分析**\n3. **競合比較マトリクス**（表形式）\n   | 項目 | 自社 | 競合A | 競合B | ... |\n4. **各社SWOT分析**\n5. **ポジショニングマップ**（テキスト描写）\n6. **差別化戦略の提案**（3-5つ）\n7. **リスクと機会**\n8. **推奨アクション**（優先度順）\n\n## ルール\n- 分析観点に応じて深掘りする項目を変える\n- 客観的な分析を心がけ、根拠のない推測は「推定」と明記する\n- 具体的で実行可能な提案を含める\n- 機密情報の取扱いに注意する",
            "自社情報:\n{{#" + make_node_id(A, 1) + ".own_company_info#}}\n\n競合企業:\n{{#" + make_node_id(A, 1) + ".competitors#}}\n\n業界: {{#" + make_node_id(A, 1) + ".industry#}}\n分析観点: {{#" + make_node_id(A, 1) + ".analysis_focus#}}",
            temp=0.4, max_tokens=8192),
        tt_node(A, 5, 1280, 182, "出力整形", "レポートにメタ情報を付与",
            "# 競合分析レポート\n\n**業界**: {{ industry }}\n**分析観点**: {{ analysis_focus }}\n\n---\n\n{{ analysis_report }}\n\n---\n*AIが生成した分析レポートです。戦略的意思決定には追加調査をお勧めします。*",
            [
                {"value_selector": [make_node_id(A, 4), "text"], "variable": "analysis_report"},
                {"value_selector": [make_node_id(A, 1), "industry"], "variable": "industry"},
                {"value_selector": [make_node_id(A, 1), "analysis_focus"], "variable": "analysis_focus"},
            ]),
        error_tt(A, 6, 980, 432, "競合分析レポートの生成を開始できませんでした。",
                 "- 自社情報は20文字以上で入力してください\n- 競合企業情報は10文字以上で入力してください\n- 不正な文字列は使用できません", 2),
        end_node(A, 7, 1580, 282, [
            {"value_selector": [make_node_id(A, 5), "output"], "variable": "analysis_result"},
            {"value_selector": [make_node_id(A, 6), "output"], "variable": "error_message"},
        ]),
    ]
    edges_list = [
        edge(A, 1, 2, "start", "code"), edge(A, 2, 3, "code", "if-else"),
        edge(A, 3, 4, "if-else", "llm", "true"), edge(A, 3, 6, "if-else", "template-transform", "false"),
        edge(A, 4, 5, "llm", "template-transform"), edge(A, 5, 7, "template-transform", "end"),
        edge(A, 6, 7, "template-transform", "end"),
    ]
    return build_workflow(A, "AIS-12: 競合分析レポート生成", "自社と競合企業の情報を入力すると、SWOT分析・比較マトリクス・差別化戦略を含む構造化された競合分析レポートを自動生成するワークフロー。", "\U0001F4CA", "#E8EAF6", "workflow", nodes, edges_list)


def build_ais_13():
    """AIS-13: LP/広告コピーバリエーション生成"""
    A = 13
    nodes = [
        node_base(A, 1, 80, 282, "start", "開始", "商品情報・ターゲット・訴求軸を受け取る", height=149, extra={
            "variables": [
                {"label": "product_info", "max_length": 10000, "options": [], "required": True, "type": "paragraph", "variable": "product_info"},
                {"label": "target_audience", "max_length": 500, "options": [], "required": True, "type": "text-input", "variable": "target_audience"},
                {"label": "appeal_axis", "max_length": 48, "options": ["機能・スペック訴求", "価格・コスパ訴求", "感情・ストーリー訴求", "権威・実績訴求", "緊急性・限定訴求"], "required": True, "type": "select", "variable": "appeal_axis"},
                {"label": "num_variations", "max_length": 48, "options": ["3案", "5案", "10案"], "required": True, "type": "select", "variable": "num_variations"},
            ]
        }),
        code_node(A, 2, 380, 282, "入力検証", "商品情報の文字数チェックとインジェクション検出",
            INJECTION_CODE.format(
                params="product_info: str, target_audience: str",
                checks='    if len(product_info.strip()) < 20:\n        issues.append("商品情報が短すぎます（20文字以上必要）")\n    if not target_audience.strip():\n        issues.append("ターゲット顧客層が空です")',
                combined_var="product_info + ' ' + target_audience"
            ),
            [
                {"value_selector": [make_node_id(A, 1), "product_info"], "variable": "product_info"},
                {"value_selector": [make_node_id(A, 1), "target_audience"], "variable": "target_audience"},
            ],
            {"is_valid": {"type": "string"}, "error_message": {"type": "string"}}
        ),
        ifelse_node(A, 3, 680, 282, "検証結果分岐", "入力検証結果で分岐する", 2, "is_valid"),
        llm_node(A, 4, 980, 182, "コピーバリエーション生成", "指定数のLP/広告コピーバリエーションを生成する",
            "あなたはダイレクトレスポンスのコピーライターです。商品情報とターゲット・訴求軸に基づいて、A/Bテスト用のコピーバリエーションを生成してください。\n\n## 各バリエーションの構成\n- **ヘッドライン**（30字以内）\n- **サブヘッド**（60字以内）\n- **ボディコピー**（100-200字）\n- **CTA文言**（15字以内）\n- **訴求ポイント**: なぜこの切り口が有効か（一行解説）\n\n## ルール\n- 各バリエーションは明確に異なる切り口にする\n- 訴求軸を基本としつつ、バリエーション内で角度を変える\n- 具体的な数値や事例を可能な限り含める\n- 広告審査に抵触しない表現を使用する（誇大表現を避ける）\n- ターゲットのペインポイントに直接語りかける",
            "商品情報:\n{{#" + make_node_id(A, 1) + ".product_info#}}\n\nターゲット: {{#" + make_node_id(A, 1) + ".target_audience#}}\n訴求軸: {{#" + make_node_id(A, 1) + ".appeal_axis#}}\n生成数: {{#" + make_node_id(A, 1) + ".num_variations#}}",
            temp=0.8, max_tokens=8192),
        tt_node(A, 5, 1280, 182, "出力整形", "コピーバリエーションにメタ情報を付与",
            "# LP/広告コピー A/Bテスト用バリエーション\n\n**ターゲット**: {{ target_audience }}\n**訴求軸**: {{ appeal_axis }}\n**生成数**: {{ num_variations }}\n\n---\n\n{{ copy_variations }}\n\n---\n*AIが生成したコピーです。薬機法・景品表示法等の法令遵守を確認してからご使用ください。*",
            [
                {"value_selector": [make_node_id(A, 4), "text"], "variable": "copy_variations"},
                {"value_selector": [make_node_id(A, 1), "target_audience"], "variable": "target_audience"},
                {"value_selector": [make_node_id(A, 1), "appeal_axis"], "variable": "appeal_axis"},
                {"value_selector": [make_node_id(A, 1), "num_variations"], "variable": "num_variations"},
            ]),
        error_tt(A, 6, 980, 432, "コピーバリエーションの生成を開始できませんでした。",
                 "- 商品情報は20文字以上で入力してください\n- ターゲット顧客層を入力してください", 2),
        end_node(A, 7, 1580, 282, [
            {"value_selector": [make_node_id(A, 5), "output"], "variable": "copy_result"},
            {"value_selector": [make_node_id(A, 6), "output"], "variable": "error_message"},
        ]),
    ]
    edges_list = [
        edge(A, 1, 2, "start", "code"), edge(A, 2, 3, "code", "if-else"),
        edge(A, 3, 4, "if-else", "llm", "true"), edge(A, 3, 6, "if-else", "template-transform", "false"),
        edge(A, 4, 5, "llm", "template-transform"), edge(A, 5, 7, "template-transform", "end"),
        edge(A, 6, 7, "template-transform", "end"),
    ]
    return build_workflow(A, "AIS-13: LP/広告コピーA/Bテスト生成", "商品情報とターゲットを入力すると、A/Bテスト用のLP/広告コピーバリエーションを一括生成するワークフロー。Unbounce/Persadoに対抗。", "\U0001F3AF", "#FCE4EC", "workflow", nodes, edges_list)


def build_ais_14():
    """AIS-14: VOC分析・感情分析レポート"""
    A = 14
    nodes = [
        node_base(A, 1, 80, 282, "start", "開始", "顧客の声データと分析観点を受け取る", height=149, extra={
            "variables": [
                {"label": "voc_data", "max_length": 999999, "options": [], "required": True, "type": "paragraph", "variable": "voc_data"},
                {"label": "data_source", "max_length": 48, "options": ["アンケート回答", "カスタマーレビュー", "SNS投稿", "問い合わせログ", "インタビュー記録"], "required": True, "type": "select", "variable": "data_source"},
                {"label": "analysis_goal", "max_length": 48, "options": ["総合分析", "改善ポイント抽出", "ポジティブ要因特定", "解約理由分析", "競合比較分析"], "required": True, "type": "select", "variable": "analysis_goal"},
            ]
        }),
        code_node(A, 2, 380, 282, "入力検証", "VOCデータの文字数チェックとインジェクション検出",
            INJECTION_CODE.format(
                params="voc_data: str",
                checks='    if len(voc_data.strip()) < 50:\n        issues.append("VOCデータが短すぎます（50文字以上必要）")\n    if len(voc_data) > 500000:\n        issues.append("VOCデータが長すぎます（500,000文字以下にしてください）")',
                combined_var="voc_data"
            ),
            [{"value_selector": [make_node_id(A, 1), "voc_data"], "variable": "voc_data"}],
            {"is_valid": {"type": "string"}, "error_message": {"type": "string"}}
        ),
        ifelse_node(A, 3, 680, 282, "検証結果分岐", "入力検証結果で分岐する", 2, "is_valid"),
        llm_node(A, 4, 980, 132, "感情分類・トピック抽出", "各VOCエントリの感情とトピックを分類する",
            "あなたはVOC分析の専門家です。顧客の声データを分析し、以下を抽出してください。\n\n## 出力フォーマット\n### 感情分布\n| 感情 | 件数 | 割合 |\n|---|---|---|\n| ポジティブ | X | X% |\n| ニュートラル | X | X% |\n| ネガティブ | X | X% |\n\n### トピック別分類\n| トピック | 件数 | 代表的な声 | 感情傾向 |\n\n### キーワード頻出ランキング\n上位10キーワードとその文脈\n\n## ルール\n- データに存在しない情報を追加しない\n- 定量的な集計を心がける\n- 個人を特定できる情報は匿名化する",
            "データソース: {{#" + make_node_id(A, 1) + ".data_source#}}\n分析目的: {{#" + make_node_id(A, 1) + ".analysis_goal#}}\n\nVOCデータ:\n{{#" + make_node_id(A, 1) + ".voc_data#}}",
            temp=0.2, max_tokens=8192),
        llm_node(A, 5, 980, 382, "洞察・提案生成", "分析結果から具体的なアクション提案を生成する",
            "あなたはCX（カスタマーエクスペリエンス）コンサルタントです。VOC分析結果に基づいて、実行可能な改善提案を作成してください。\n\n## 出力フォーマット\n### インサイト（3-5個）\n各インサイトについて: 発見事項 → 根拠となる声 → ビジネスインパクト\n\n### 改善アクション（優先度順）\n| # | アクション | 期待効果 | 難易度 | 優先度 |\n\n### 要注意シグナル\n早急に対応が必要な問題点\n\n## ルール\n- 具体的で実行可能な提案にする\n- 定量的な根拠を可能な限り含める\n- 推測と事実を明確に区別する",
            "分析目的: {{#" + make_node_id(A, 1) + ".analysis_goal#}}\n\nVOC分析結果:\n{{#" + make_node_id(A, 4) + ".text#}}",
            temp=0.3, max_tokens=4096),
        node_base(A, 6, 1280, 282, "variable-aggregator", "結果統合", "分析結果と提案を統合する", height=89, extra={
            "advanced_settings": {"group_enabled": False},
            "output_type": "string",
            "variables": [[make_node_id(A, 4), "text"], [make_node_id(A, 5), "text"]]
        }),
        tt_node(A, 7, 1580, 282, "レポート整形", "VOC分析レポートとしてフォーマットする",
            "# VOC分析レポート\n\n**データソース**: {{ data_source }}\n**分析目的**: {{ analysis_goal }}\n\n---\n\n{{ combined_analysis }}\n\n---\n*AIによる自動分析です。重要な意思決定には生データの確認をお勧めします。*",
            [
                {"value_selector": [make_node_id(A, 6), "output"], "variable": "combined_analysis"},
                {"value_selector": [make_node_id(A, 1), "data_source"], "variable": "data_source"},
                {"value_selector": [make_node_id(A, 1), "analysis_goal"], "variable": "analysis_goal"},
            ]),
        error_tt(A, 8, 980, 532, "VOC分析を開始できませんでした。",
                 "- VOCデータは50文字以上で入力してください\n- 500,000文字以下にしてください", 2),
        end_node(A, 9, 1880, 282, [
            {"value_selector": [make_node_id(A, 7), "output"], "variable": "voc_report"},
            {"value_selector": [make_node_id(A, 8), "output"], "variable": "error_message"},
        ]),
    ]
    edges_list = [
        edge(A, 1, 2, "start", "code"), edge(A, 2, 3, "code", "if-else"),
        edge(A, 3, 4, "if-else", "llm", "true"), edge(A, 3, 5, "if-else", "llm", "true"),
        edge(A, 3, 8, "if-else", "template-transform", "false"),
        edge(A, 4, 6, "llm", "variable-aggregator"), edge(A, 5, 6, "llm", "variable-aggregator"),
        edge(A, 6, 7, "variable-aggregator", "template-transform"),
        edge(A, 7, 9, "template-transform", "end"), edge(A, 8, 9, "template-transform", "end"),
    ]
    return build_workflow(A, "AIS-14: VOC分析・感情分析レポート", "顧客の声データ（アンケート/レビュー/SNS等）を入力すると、感情分析・トピック分類・改善アクション提案を含む構造化レポートを自動生成するワークフロー。", "\U0001F4AC", "#E8F5E9", "workflow", nodes, edges_list)


def build_standard_workflow(ais_num, name, desc, icon, icon_bg, start_vars, validation_params, validation_checks, validation_combined, system_prompt, user_prompt, output_title, output_template_vars, guide_text, temp=0.3, max_tokens=4096):
    """標準パターン: Start → Code → IF-ELSE → LLM → TT → End"""
    A = ais_num
    nodes = [
        node_base(A, 1, 80, 282, "start", "開始", "入力パラメータを受け取る", height=149, extra={"variables": start_vars}),
        code_node(A, 2, 380, 282, "入力検証", "入力テキストの長さチェックとインジェクション検出を行う",
            INJECTION_CODE.format(params=validation_params, checks=validation_checks, combined_var=validation_combined),
            [{"value_selector": [make_node_id(A, 1), v.split(":")[0].strip()], "variable": v.split(":")[0].strip()} for v in validation_params.split(", ")],
            {"is_valid": {"type": "string"}, "error_message": {"type": "string"}}
        ),
        ifelse_node(A, 3, 680, 282, "検証結果分岐", "入力検証結果で分岐する", 2, "is_valid"),
        llm_node(A, 4, 980, 182, "AI生成", desc, system_prompt, user_prompt, temp=temp, max_tokens=max_tokens),
        tt_node(A, 5, 1280, 182, "出力整形", "生成結果にメタ情報を付与して整形する", output_title, output_template_vars),
        error_tt(A, 6, 980, 432, f"{name}の生成を開始できませんでした。", guide_text, 2),
        end_node(A, 7, 1580, 282, [
            {"value_selector": [make_node_id(A, 5), "output"], "variable": "result"},
            {"value_selector": [make_node_id(A, 6), "output"], "variable": "error_message"},
        ]),
    ]
    edges_list = [
        edge(A, 1, 2, "start", "code"), edge(A, 2, 3, "code", "if-else"),
        edge(A, 3, 4, "if-else", "llm", "true"), edge(A, 3, 6, "if-else", "template-transform", "false"),
        edge(A, 4, 5, "llm", "template-transform"), edge(A, 5, 7, "template-transform", "end"),
        edge(A, 6, 7, "template-transform", "end"),
    ]
    return build_workflow(A, f"AIS-{A:02d}: {name}", desc, icon, icon_bg, "workflow", nodes, edges_list)


# ── AIS-15: 問い合わせ自動分類・優先度判定 ──
def build_ais_15():
    A = 15
    return build_standard_workflow(A, "問い合わせ自動分類・優先度判定",
        "問い合わせテキストを入力すると、カテゴリ分類・優先度判定・推奨対応を自動生成するワークフロー。Zendesk AI/ServiceNowに対抗。",
        "\U0001F4CB", "#E0F7FA",
        [
            {"label": "inquiry_text", "max_length": 50000, "options": [], "required": True, "type": "paragraph", "variable": "inquiry_text"},
            {"label": "channel", "max_length": 48, "options": ["メール", "チャット", "電話メモ", "Webフォーム", "SNS"], "required": True, "type": "select", "variable": "channel"},
        ],
        "inquiry_text: str",
        '    if len(inquiry_text.strip()) < 10:\n        issues.append("問い合わせテキストが短すぎます（10文字以上必要）")',
        "inquiry_text",
        "あなたはカスタマーサポートのトリアージ専門AIです。問い合わせ内容を分析し、以下を判定してください。\n\n## 出力フォーマット\n### 分類結果\n| 項目 | 判定 |\n|---|---|\n| カテゴリ | 技術的問題/料金・請求/アカウント/配送/その他 |\n| サブカテゴリ | （詳細分類） |\n| 優先度 | 緊急/高/中/低 |\n| 感情 | 怒り/不満/普通/満足 |\n| エスカレーション | 必要/不要 |\n\n### 推奨対応\n- 初動対応案（テンプレート回答のドラフト）\n- 対応時の注意点\n- 参照すべきナレッジ記事のキーワード\n\n### 判定根拠\n- なぜこの優先度と判断したか\n\n## ルール\n- 顧客の感情に配慮した対応案を作成する\n- 個人情報は出力しない\n- エスカレーション基準: クレーム・法的言及・繰り返し問い合わせ・VIP顧客",
        "チャネル: {{#" + make_node_id(A, 1) + ".channel#}}\n\n問い合わせ内容:\n{{#" + make_node_id(A, 1) + ".inquiry_text#}}",
        "# 問い合わせ分類・優先度判定結果\n\n**チャネル**: {{ channel }}\n\n---\n\n{{ classification_result }}\n\n---\n*AIによる自動分類です。最終判断はサポート担当者が行ってください。*",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "classification_result"},
            {"value_selector": [make_node_id(A, 1), "channel"], "variable": "channel"},
        ],
        "- 問い合わせテキストは10文字以上で入力してください\n- 不正な文字列は使用できません",
        temp=0.2)


# ── AIS-16: 利用規約・プライバシーポリシー生成 ──
def build_ais_16():
    A = 16
    return build_standard_workflow(A, "利用規約・プライバシーポリシー生成",
        "サービス概要を入力すると、利用規約・プライバシーポリシーのドラフトを自動生成するワークフロー。Termly/iubendaに対抗。",
        "\U0001F4DC", "#E8EAF6",
        [
            {"label": "service_description", "max_length": 20000, "options": [], "required": True, "type": "paragraph", "variable": "service_description"},
            {"label": "document_type", "max_length": 48, "options": ["利用規約", "プライバシーポリシー", "両方"], "required": True, "type": "select", "variable": "document_type"},
            {"label": "business_type", "max_length": 48, "options": ["SaaS/Webサービス", "ECサイト", "モバイルアプリ", "コンサルティング", "メディア/コンテンツ"], "required": True, "type": "select", "variable": "business_type"},
            {"label": "data_handling", "max_length": 10000, "options": [], "required": False, "type": "paragraph", "variable": "data_handling"},
        ],
        "service_description: str",
        '    if len(service_description.strip()) < 30:\n        issues.append("サービス概要が短すぎます（30文字以上必要）")',
        "service_description",
        "あなたは企業法務の専門家です。サービス概要に基づいて、日本法に準拠した利用規約またはプライバシーポリシーのドラフトを作成してください。\n\n## 利用規約の構成\n第1条 総則 / 第2条 定義 / 第3条 サービス内容 / 第4条 利用登録 / 第5条 禁止事項 / 第6条 知的財産権 / 第7条 免責事項 / 第8条 利用制限・登録抹消 / 第9条 サービス変更・中止 / 第10条 利用規約の変更 / 第11条 個人情報 / 第12条 準拠法・管轄\n\n## プライバシーポリシーの構成\n1. 基本方針 / 2. 収集する個人情報 / 3. 利用目的 / 4. 第三者提供 / 5. 安全管理措置 / 6. 委託先の監督 / 7. 開示・訂正・削除 / 8. Cookie等の利用 / 9. お問い合わせ窓口 / 10. 改定\n\n## ルール\n- 個人情報保護法（2022年改正）に準拠する\n- ビジネスタイプに応じた特有の条項を含める\n- 法的助言ではなくドラフトである旨を明記する\n- 「本ドラフトは参考用であり、弁護士の確認を推奨します」の注記を含める",
        "サービス概要:\n{{#" + make_node_id(A, 1) + ".service_description#}}\n\n文書タイプ: {{#" + make_node_id(A, 1) + ".document_type#}}\nビジネスタイプ: {{#" + make_node_id(A, 1) + ".business_type#}}\nデータ取扱い:\n{{#" + make_node_id(A, 1) + ".data_handling#}}",
        "# {{ document_type }} ドラフト\n\n**ビジネスタイプ**: {{ business_type }}\n\n---\n\n{{ legal_document }}\n\n---\n> **免責事項**: 本文書はAIが生成したドラフトであり、法的助言ではありません。正式な利用にあたっては必ず弁護士の確認を受けてください。",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "legal_document"},
            {"value_selector": [make_node_id(A, 1), "document_type"], "variable": "document_type"},
            {"value_selector": [make_node_id(A, 1), "business_type"], "variable": "business_type"},
        ],
        "- サービス概要は30文字以上で入力してください\n- 不正な文字列は使用できません",
        temp=0.2, max_tokens=8192)


# ── AIS-17〜25: 残りのワークフロー ──
def build_ais_17():
    A = 17
    return build_standard_workflow(A, "コンプライアンスチェックリスト生成",
        "業界・規制情報を入力すると、対応すべきコンプライアンス項目チェックリストを自動生成するワークフロー。",
        "\U00002705", "#E8F5E9",
        [
            {"label": "business_description", "max_length": 20000, "options": [], "required": True, "type": "paragraph", "variable": "business_description"},
            {"label": "regulation_area", "max_length": 48, "options": ["個人情報保護", "景品表示法", "特定商取引法", "労働法", "金融商品取引法", "薬機法", "下請法", "総合チェック"], "required": True, "type": "select", "variable": "regulation_area"},
        ],
        "business_description: str",
        '    if len(business_description.strip()) < 20:\n        issues.append("事業内容が短すぎます（20文字以上必要）")',
        "business_description",
        "あなたは日本の企業コンプライアンスの専門家です。事業内容と対象規制に基づいて、包括的なコンプライアンスチェックリストを作成してください。\n\n## 出力フォーマット\n### チェックリスト\n| # | チェック項目 | 対象法令 | 重要度 | 対応状況 | 備考 |\n|---|---|---|---|---|---|\n| 1 | （具体的なチェック項目） | （法令名） | 高/中/低 | □未確認 | （補足） |\n\n### 対応推奨事項\n優先度の高い項目から順に、具体的な対応手順を記載\n\n### 参考法令・ガイドライン\n関連する法令とガイドラインの一覧\n\n## ルール\n- 最新の法改正を考慮する\n- 具体的で実行可能なチェック項目にする\n- 法的助言ではなくチェックリストの提供である旨を明記\n- 業界固有の規制要件を含める",
        "事業内容:\n{{#" + make_node_id(A, 1) + ".business_description#}}\n\n規制分野: {{#" + make_node_id(A, 1) + ".regulation_area#}}",
        "# コンプライアンスチェックリスト\n\n**規制分野**: {{ regulation_area }}\n\n---\n\n{{ checklist }}\n\n---\n> 本チェックリストはAI生成の参考資料です。正式なコンプライアンス対応は法務部・顧問弁護士にご相談ください。",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "checklist"},
            {"value_selector": [make_node_id(A, 1), "regulation_area"], "variable": "regulation_area"},
        ],
        "- 事業内容は20文字以上で入力してください",
        temp=0.2, max_tokens=8192)


def build_ais_18():
    A = 18
    return build_standard_workflow(A, "履歴書スクリーニング・評価",
        "求人要件と候補者の履歴書/職務経歴書を入力すると、マッチ度評価・強み/懸念点・面接ポイントを自動生成するワークフロー。HireVue/Pymetricsに対抗。",
        "\U0001F4DD", "#FFF3E0",
        [
            {"label": "job_requirements", "max_length": 20000, "options": [], "required": True, "type": "paragraph", "variable": "job_requirements"},
            {"label": "resume_text", "max_length": 50000, "options": [], "required": True, "type": "paragraph", "variable": "resume_text"},
            {"label": "evaluation_focus", "max_length": 48, "options": ["総合評価", "スキルマッチ重視", "カルチャーフィット重視", "成長ポテンシャル重視"], "required": True, "type": "select", "variable": "evaluation_focus"},
        ],
        "job_requirements: str, resume_text: str",
        '    if len(job_requirements.strip()) < 20:\n        issues.append("求人要件が短すぎます（20文字以上必要）")\n    if len(resume_text.strip()) < 50:\n        issues.append("履歴書/職務経歴書が短すぎます（50文字以上必要）")',
        "job_requirements + ' ' + resume_text",
        "あなたは採用のプロフェッショナルです。求人要件と候補者の履歴書を照合し、公正な評価を行ってください。\n\n## 出力フォーマット\n### マッチ度スコア\n**総合**: X/100点\n| 評価項目 | スコア | 根拠 |\n|---|---|---|\n| 必須スキル | X/25 | |\n| 経験年数・実績 | X/25 | |\n| 業界知識 | X/25 | |\n| カルチャーフィット | X/25 | |\n\n### 強み（3-5個）\n### 懸念点（0-3個）\n### 面接で確認すべきポイント（3-5個）\n### 推奨: 合格/保留/不合格\n\n## ルール\n- 年齢・性別・国籍等による差別的評価は絶対に行わない\n- 客観的な事実に基づく評価を行う\n- 不足情報は「確認が必要」と明記する\n- 最終判断は人事担当者が行う旨を注記する",
        "求人要件:\n{{#" + make_node_id(A, 1) + ".job_requirements#}}\n\n評価観点: {{#" + make_node_id(A, 1) + ".evaluation_focus#}}\n\n履歴書/職務経歴書:\n{{#" + make_node_id(A, 1) + ".resume_text#}}",
        "# 履歴書スクリーニング結果\n\n**評価観点**: {{ evaluation_focus }}\n\n---\n\n{{ screening_result }}\n\n---\n> AIによる参考評価です。採用判断は必ず複数の人事担当者で行ってください。\n> 差別的な判断基準に基づく評価は含まれていません。",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "screening_result"},
            {"value_selector": [make_node_id(A, 1), "evaluation_focus"], "variable": "evaluation_focus"},
        ],
        "- 求人要件は20文字以上で入力してください\n- 履歴書/職務経歴書は50文字以上で入力してください",
        temp=0.2)


def build_ais_19():
    A = 19
    return build_standard_workflow(A, "面接質問自動生成",
        "ポジション情報と候補者プロフィールを入力すると、構造化面接用の質問セットを自動生成するワークフロー。",
        "\U0001F3A4", "#F3E5F5",
        [
            {"label": "position_info", "max_length": 10000, "options": [], "required": True, "type": "paragraph", "variable": "position_info"},
            {"label": "candidate_profile", "max_length": 10000, "options": [], "required": False, "type": "paragraph", "variable": "candidate_profile"},
            {"label": "interview_type", "max_length": 48, "options": ["一次面接（カルチャーフィット）", "二次面接（スキル確認）", "最終面接（役員面接）", "技術面接", "ケース面接"], "required": True, "type": "select", "variable": "interview_type"},
        ],
        "position_info: str",
        '    if len(position_info.strip()) < 20:\n        issues.append("ポジション情報が短すぎます（20文字以上必要）")',
        "position_info",
        "あなたは採用面接の専門家です。構造化面接の手法に基づいて、効果的な面接質問セットを作成してください。\n\n## 出力フォーマット\n### アイスブレイク質問（2問）\n### 行動面接質問（STAR法）（5問）\n各質問にフォローアップ質問と評価ポイントを付記\n### 状況判断質問（3問）\n### 動機・キャリア質問（3問）\n### 逆質問への準備（面接官が回答すべきFAQ 3問）\n\n### 評価シート\n| 評価項目 | 質問# | 評価基準（1-5） | メモ欄 |\n\n## ルール\n- 差別的な質問（家族構成・宗教・出身地等）は絶対に含めない\n- 面接タイプに応じた質問レベルにする\n- 候補者プロフィールがあれば、経歴に基づく深掘り質問を含める\n- 回答の評価基準を明確にする",
        "ポジション情報:\n{{#" + make_node_id(A, 1) + ".position_info#}}\n\n面接タイプ: {{#" + make_node_id(A, 1) + ".interview_type#}}\n\n候補者プロフィール:\n{{#" + make_node_id(A, 1) + ".candidate_profile#}}",
        "# 面接質問セット\n\n**面接タイプ**: {{ interview_type }}\n\n---\n\n{{ interview_questions }}\n\n---\n*AIが生成した質問セットです。法令遵守を確認してからご使用ください。*",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "interview_questions"},
            {"value_selector": [make_node_id(A, 1), "interview_type"], "variable": "interview_type"},
        ],
        "- ポジション情報は20文字以上で入力してください",
        temp=0.5)


def build_ais_20():
    A = 20
    return build_standard_workflow(A, "人事評価コメント生成",
        "評価対象者の実績と評価基準を入力すると、公正で具体的な評価コメントを自動生成するワークフロー。HRBrain AIに対抗。",
        "\U0001F4DD", "#E0F2F1",
        [
            {"label": "employee_achievements", "max_length": 20000, "options": [], "required": True, "type": "paragraph", "variable": "employee_achievements"},
            {"label": "evaluation_criteria", "max_length": 10000, "options": [], "required": True, "type": "paragraph", "variable": "evaluation_criteria"},
            {"label": "evaluation_period", "max_length": 48, "options": ["四半期", "上半期", "下半期", "年間"], "required": True, "type": "select", "variable": "evaluation_period"},
            {"label": "rating", "max_length": 48, "options": ["S（卓越）", "A（期待以上）", "B（期待通り）", "C（要改善）", "D（不十分）"], "required": True, "type": "select", "variable": "rating"},
        ],
        "employee_achievements: str, evaluation_criteria: str",
        '    if len(employee_achievements.strip()) < 20:\n        issues.append("実績情報が短すぎます（20文字以上必要）")\n    if len(evaluation_criteria.strip()) < 10:\n        issues.append("評価基準が短すぎます（10文字以上必要）")',
        "employee_achievements + ' ' + evaluation_criteria",
        "あなたは人事評価の専門家です。従業員の実績と評価基準に基づいて、公正で建設的な評価コメントを作成してください。\n\n## 出力フォーマット\n### 総合評価コメント（200-300字）\n### 項目別評価\n| 評価項目 | 評価 | コメント |\n\n### 具体的な成果と貢献（箇条書き）\n### 今後の成長に向けた期待・助言\n### 次期の目標提案（SMART形式で3つ）\n\n## ルール\n- 具体的な事実と数値に基づく評価を行う\n- ポジティブフィードバックとフィードフォワードを適切にバランスする\n- 人格否定や曖昧な表現は避ける\n- 評価ランクに整合するコメントにする\n- 個人の属性（年齢・性別等）に基づく評価は行わない",
        "評価期間: {{#" + make_node_id(A, 1) + ".evaluation_period#}}\n評価ランク: {{#" + make_node_id(A, 1) + ".rating#}}\n\n評価基準:\n{{#" + make_node_id(A, 1) + ".evaluation_criteria#}}\n\n実績情報:\n{{#" + make_node_id(A, 1) + ".employee_achievements#}}",
        "# 人事評価コメント\n\n**評価期間**: {{ evaluation_period }}\n**評価ランク**: {{ rating }}\n\n---\n\n{{ evaluation_comment }}\n\n---\n*AIが生成した評価コメントのドラフトです。最終的な評価は上長・人事部門の判断で確定してください。*",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "evaluation_comment"},
            {"value_selector": [make_node_id(A, 1), "evaluation_period"], "variable": "evaluation_period"},
            {"value_selector": [make_node_id(A, 1), "rating"], "variable": "rating"},
        ],
        "- 実績情報は20文字以上で入力してください\n- 評価基準は10文字以上で入力してください",
        temp=0.3)


def build_ais_21():
    A = 21
    return build_standard_workflow(A, "財務分析レポート生成",
        "財務データを入力すると、経営指標分析・トレンド解説・改善提案を含む財務レポートを自動生成するワークフロー。",
        "\U0001F4B0", "#FFF9C4",
        [
            {"label": "financial_data", "max_length": 100000, "options": [], "required": True, "type": "paragraph", "variable": "financial_data"},
            {"label": "report_type", "max_length": 48, "options": ["月次レポート", "四半期レポート", "年次レポート", "予実分析", "資金繰り分析"], "required": True, "type": "select", "variable": "report_type"},
            {"label": "comparison_period", "max_length": 256, "options": [], "required": False, "type": "text-input", "variable": "comparison_period"},
        ],
        "financial_data: str",
        '    if len(financial_data.strip()) < 50:\n        issues.append("財務データが短すぎます（50文字以上必要）")',
        "financial_data",
        "あなたは公認会計士レベルの財務分析専門AIです。提供された財務データに基づいて、経営判断に役立つ分析レポートを作成してください。\n\n## 出力フォーマット\n### エグゼクティブサマリー（3行）\n### 主要KPI\n| 指標 | 今期 | 前期 | 増減 | 評価 |\n\n### 収益性分析\n- 売上総利益率/営業利益率/経常利益率\n### 安全性分析\n- 流動比率/自己資本比率\n### 効率性分析\n- 総資産回転率/棚卸資産回転率\n### トレンド分析\n前期比較・業界平均との比較\n### 改善提案（3-5項目）\n### 注意すべきリスク\n\n## ルール\n- データに基づく客観的な分析を行う\n- 推測と事実を明確に区別する\n- 投資助言ではないことを明記する\n- 機密性の高い数値は適切に取り扱う",
        "レポートタイプ: {{#" + make_node_id(A, 1) + ".report_type#}}\n比較期間: {{#" + make_node_id(A, 1) + ".comparison_period#}}\n\n財務データ:\n{{#" + make_node_id(A, 1) + ".financial_data#}}",
        "# 財務分析レポート\n\n**レポートタイプ**: {{ report_type }}\n\n---\n\n{{ financial_report }}\n\n---\n> 本レポートはAIによる参考分析です。投資助言や会計上の判断には専門家にご相談ください。",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "financial_report"},
            {"value_selector": [make_node_id(A, 1), "report_type"], "variable": "report_type"},
        ],
        "- 財務データは50文字以上で入力してください",
        temp=0.2, max_tokens=8192)


def build_ais_22():
    A = 22
    return build_standard_workflow(A, "見積書ドラフト生成",
        "顧客要件と商品/サービス情報を入力すると、見積書のドラフトテキストを自動生成するワークフロー。営業事務効率化ツール。",
        "\U0001F4B4", "#E0F2F1",
        [
            {"label": "client_requirements", "max_length": 20000, "options": [], "required": True, "type": "paragraph", "variable": "client_requirements"},
            {"label": "product_catalog", "max_length": 50000, "options": [], "required": True, "type": "paragraph", "variable": "product_catalog"},
            {"label": "pricing_strategy", "max_length": 48, "options": ["標準価格", "ボリュームディスカウント", "キャンペーン価格", "カスタム見積"], "required": True, "type": "select", "variable": "pricing_strategy"},
        ],
        "client_requirements: str, product_catalog: str",
        '    if len(client_requirements.strip()) < 20:\n        issues.append("顧客要件が短すぎます（20文字以上必要）")\n    if len(product_catalog.strip()) < 20:\n        issues.append("商品/サービス情報が短すぎます（20文字以上必要）")',
        "client_requirements + ' ' + product_catalog",
        "あなたは営業事務の専門家です。顧客要件と商品カタログに基づいて、見積書のドラフトを作成してください。\n\n## 出力フォーマット\n### 見積書\n**宛先**: （顧客名）\n**見積番号**: （自動生成の参考番号）\n**有効期限**: 発行日から30日間\n\n| # | 品目/サービス名 | 数量 | 単価 | 金額 |\n|---|---|---|---|---|\n| 1 | | | | |\n\n**小計**: ¥XXX\n**消費税（10%）**: ¥XXX\n**合計**: ¥XXX\n\n### 備考\n- 納期・支払条件・特記事項\n\n### 補足説明\n- 各項目の選定理由\n- 代替案がある場合の提案\n\n## ルール\n- 金額は税抜表示を基本とし、消費税を別記する\n- 顧客要件に最も適した商品を選定する\n- 価格戦略に沿った価格設定にする\n- 正式な見積書ではなくドラフトであることを明記する",
        "顧客要件:\n{{#" + make_node_id(A, 1) + ".client_requirements#}}\n\n価格戦略: {{#" + make_node_id(A, 1) + ".pricing_strategy#}}\n\n商品/サービスカタログ:\n{{#" + make_node_id(A, 1) + ".product_catalog#}}",
        "# 見積書ドラフト\n\n**価格戦略**: {{ pricing_strategy }}\n\n---\n\n{{ estimate_draft }}\n\n---\n> 本見積は AIが生成したドラフトです。正式な見積書として使用する前に、価格・数量・条件を必ず確認してください。",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "estimate_draft"},
            {"value_selector": [make_node_id(A, 1), "pricing_strategy"], "variable": "pricing_strategy"},
        ],
        "- 顧客要件・商品情報はそれぞれ20文字以上で入力してください",
        temp=0.3)


def build_ais_23():
    A = 23
    return build_standard_workflow(A, "Text-to-SQL クエリ生成",
        "自然言語の質問とテーブル定義を入力すると、SQLクエリを自動生成・解説するワークフロー。AI2SQL/Outerbaseに対抗するデータ民主化ツール。",
        "\U0001F5C4", "#E3F2FD",
        [
            {"label": "natural_language_query", "max_length": 5000, "options": [], "required": True, "type": "paragraph", "variable": "natural_language_query"},
            {"label": "table_schema", "max_length": 50000, "options": [], "required": True, "type": "paragraph", "variable": "table_schema"},
            {"label": "db_type", "max_length": 48, "options": ["PostgreSQL", "MySQL", "SQLite", "BigQuery", "SQL Server"], "required": True, "type": "select", "variable": "db_type"},
        ],
        "natural_language_query: str, table_schema: str",
        '    if len(natural_language_query.strip()) < 5:\n        issues.append("質問が短すぎます（5文字以上必要）")\n    if len(table_schema.strip()) < 10:\n        issues.append("テーブル定義が短すぎます（10文字以上必要）")',
        "natural_language_query + ' ' + table_schema",
        "あなたはデータベースエンジニアです。自然言語の質問をSQLクエリに変換してください。\n\n## 出力フォーマット\n### 生成されたSQL\n```sql\n（SQLクエリ）\n```\n\n### クエリの解説\n- このクエリが何をしているかの説明\n- 使用しているテーブルとカラムの一覧\n- JOINやフィルタ条件の説明\n\n### パフォーマンス注意点\n- 推奨インデックス\n- 大規模データでの注意点\n\n### 代替クエリ（該当する場合）\n異なるアプローチのクエリ案\n\n## ルール\n- 指定されたDB種別の方言に準拠する\n- SQLインジェクションを防ぐ安全なクエリにする\n- DELETE/DROP/TRUNCATE等の破壊的操作は生成しない（SELECTのみ）\n- テーブル定義に存在するカラムのみを使用する\n- 不明な点は仮定を明記する",
        "DB種別: {{#" + make_node_id(A, 1) + ".db_type#}}\n\nテーブル定義:\n{{#" + make_node_id(A, 1) + ".table_schema#}}\n\n質問:\n{{#" + make_node_id(A, 1) + ".natural_language_query#}}",
        "# Text-to-SQL 変換結果\n\n**DB種別**: {{ db_type }}\n\n---\n\n{{ sql_result }}\n\n---\n*AIが生成したSQLです。本番環境で実行する前に必ずレビューしてください。破壊的操作（DELETE/DROP等）は含まれていません。*",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "sql_result"},
            {"value_selector": [make_node_id(A, 1), "db_type"], "variable": "db_type"},
        ],
        "- 質問は5文字以上で入力してください\n- テーブル定義（CREATE TABLE文等）を入力してください",
        temp=0.1)


def build_ais_24():
    A = 24
    return build_standard_workflow(A, "API仕様書自動生成",
        "APIエンドポイントの概要やコードを入力すると、OpenAPI形式のAPI仕様書を自動生成するワークフロー。Readme.com/Mintlifyに対抗。",
        "\U0001F4D6", "#E8EAF6",
        [
            {"label": "api_description", "max_length": 50000, "options": [], "required": True, "type": "paragraph", "variable": "api_description"},
            {"label": "output_format", "max_length": 48, "options": ["OpenAPI 3.0 (YAML)", "Markdown", "両方"], "required": True, "type": "select", "variable": "output_format"},
            {"label": "language", "max_length": 48, "options": ["日本語", "英語"], "required": True, "type": "select", "variable": "language"},
        ],
        "api_description: str",
        '    if len(api_description.strip()) < 20:\n        issues.append("API概要が短すぎます（20文字以上必要）")',
        "api_description",
        "あなたはテクニカルライターです。API情報に基づいて、開発者向けのAPI仕様書を作成してください。\n\n## 出力フォーマット\n### エンドポイント一覧\n| メソッド | パス | 概要 |\n\n### 各エンドポイントの詳細\n#### [メソッド] /path\n**概要**: \n**リクエスト**:\n- Headers\n- Path Parameters\n- Query Parameters\n- Request Body (JSON Schema)\n\n**レスポンス**:\n- 200: 成功レスポンス（例付き）\n- 400/401/404/500: エラーレスポンス\n\n**コード例**:\n```curl\n（curlコマンド）\n```\n\n### 認証方式\n### エラーコード一覧\n### レートリミット\n\n## ルール\n- RESTful APIのベストプラクティスに準拠する\n- 具体的なリクエスト/レスポンス例を含める\n- エラーハンドリングを網羅する\n- 出力フォーマットに応じた形式で出力する",
        "API概要/コード:\n{{#" + make_node_id(A, 1) + ".api_description#}}\n\n出力フォーマット: {{#" + make_node_id(A, 1) + ".output_format#}}\n言語: {{#" + make_node_id(A, 1) + ".language#}}",
        "# API仕様書\n\n**フォーマット**: {{ output_format }}\n\n---\n\n{{ api_spec }}\n\n---\n*AIが生成したAPI仕様書です。実際のAPI動作と照合して確認してください。*",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "api_spec"},
            {"value_selector": [make_node_id(A, 1), "output_format"], "variable": "output_format"},
        ],
        "- API概要は20文字以上で入力してください",
        temp=0.2, max_tokens=8192)


def build_ais_25():
    A = 25
    return build_standard_workflow(A, "社内研修コンテンツ生成",
        "研修テーマと対象者を入力すると、教材テキスト・確認テスト・ワークシートを含む研修コンテンツを自動生成するワークフロー。EdApp/Docebo AIに対抗。",
        "\U0001F393", "#FFF9C4",
        [
            {"label": "training_topic", "max_length": 10000, "options": [], "required": True, "type": "paragraph", "variable": "training_topic"},
            {"label": "target_audience", "max_length": 48, "options": ["新入社員", "中堅社員", "管理職", "全社員", "エンジニア", "営業"], "required": True, "type": "select", "variable": "target_audience"},
            {"label": "duration", "max_length": 48, "options": ["15分", "30分", "60分", "90分", "半日"], "required": True, "type": "select", "variable": "duration"},
            {"label": "content_type", "max_length": 48, "options": ["座学（スライド用テキスト）", "ワークショップ型", "eラーニング用", "OJT用チェックリスト"], "required": True, "type": "select", "variable": "content_type"},
        ],
        "training_topic: str",
        '    if len(training_topic.strip()) < 10:\n        issues.append("研修テーマが短すぎます（10文字以上必要）")',
        "training_topic",
        "あなたは企業研修デザインの専門家です。研修テーマ・対象者・時間に基づいて、実践的な研修コンテンツを作成してください。\n\n## 出力フォーマット\n### 研修概要\n- タイトル / 目的 / 到達目標 / 所要時間\n\n### タイムテーブル\n| 時間 | 内容 | 手法 | 教材 |\n\n### 教材テキスト\n各セクションの詳細な説明テキスト（スライドノート形式）\n\n### 確認テスト（5-10問）\n選択式・記述式を混合、解答付き\n\n### ワークシート / ディスカッション課題\n### 参考資料リスト\n\n## ルール\n- 対象者のレベルに合わせた内容にする\n- アクティブラーニングの要素を含める\n- 実務に直結する事例・演習を使う\n- コンテンツタイプに応じた形式で出力する",
        "研修テーマ:\n{{#" + make_node_id(A, 1) + ".training_topic#}}\n\n対象者: {{#" + make_node_id(A, 1) + ".target_audience#}}\n所要時間: {{#" + make_node_id(A, 1) + ".duration#}}\nコンテンツ形式: {{#" + make_node_id(A, 1) + ".content_type#}}",
        "# 研修コンテンツ\n\n**対象者**: {{ target_audience }}\n**所要時間**: {{ duration }}\n**形式**: {{ content_type }}\n\n---\n\n{{ training_content }}\n\n---\n*AIが生成した研修コンテンツです。社内規程・最新情報との整合性を確認してからご使用ください。*",
        [
            {"value_selector": [make_node_id(A, 4), "text"], "variable": "training_content"},
            {"value_selector": [make_node_id(A, 1), "target_audience"], "variable": "target_audience"},
            {"value_selector": [make_node_id(A, 1), "duration"], "variable": "duration"},
            {"value_selector": [make_node_id(A, 1), "content_type"], "variable": "content_type"},
        ],
        "- 研修テーマは10文字以上で入力してください",
        temp=0.5, max_tokens=8192)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# YAML出力 & 実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LiteralStr(str):
    pass

def literal_str_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralStr, literal_str_representer)

def convert_multiline(obj):
    """Recursively convert multiline strings to LiteralStr for YAML block style"""
    if isinstance(obj, dict):
        return {k: convert_multiline(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_multiline(i) for i in obj]
    elif isinstance(obj, str) and '\n' in obj:
        return LiteralStr(obj)
    return obj

BUILDERS = {
    11: build_ais_11, 12: build_ais_12, 13: build_ais_13, 14: build_ais_14,
    15: build_ais_15, 16: build_ais_16, 17: build_ais_17, 18: build_ais_18,
    19: build_ais_19, 20: build_ais_20, 21: build_ais_21, 22: build_ais_22,
    23: build_ais_23, 24: build_ais_24, 25: build_ais_25,
}

FILENAMES = {
    11: "ais-11-email-personalizer.yml",
    12: "ais-12-competitor-analysis.yml",
    13: "ais-13-ad-copy-ab-test.yml",
    14: "ais-14-voc-sentiment-analysis.yml",
    15: "ais-15-inquiry-triage.yml",
    16: "ais-16-terms-privacy-generator.yml",
    17: "ais-17-compliance-checklist.yml",
    18: "ais-18-resume-screening.yml",
    19: "ais-19-interview-questions.yml",
    20: "ais-20-performance-review.yml",
    21: "ais-21-financial-report.yml",
    22: "ais-22-estimate-draft.yml",
    23: "ais-23-text-to-sql.yml",
    24: "ais-24-api-spec-generator.yml",
    25: "ais-25-training-content.yml",
}

if __name__ == "__main__":
    for num, builder in BUILDERS.items():
        doc = builder()
        doc = convert_multiline(doc)
        filepath = os.path.join(OUTPUT_DIR, FILENAMES[num])
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(doc, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=200)
        print(f"  Generated: {FILENAMES[num]}")

    print(f"\nAll {len(BUILDERS)} workflows generated successfully.")
