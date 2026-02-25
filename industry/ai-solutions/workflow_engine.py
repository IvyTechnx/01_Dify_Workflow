#!/usr/bin/env python3
"""
Dify ワークフロー自動生成エンジン
業界別AIソリューション YML を自動生成するための共通ヘルパー
"""
import yaml
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# YAML ヘルパー
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LiteralStr(str):
    pass

def literal_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralStr, literal_representer)

def convert_multiline(obj):
    """Recursively convert multiline strings to LiteralStr for YAML block style"""
    if isinstance(obj, dict):
        return {k: convert_multiline(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_multiline(i) for i in obj]
    elif isinstance(obj, str) and '\n' in obj:
        return LiteralStr(obj)
    return obj

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ノード ID / エッジ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def nid(ais_num, node_num):
    """AIS番号とノード番号からノードID生成"""
    return str(ais_num * 100000000000 + 50000000000000 + node_num)

def mk_edge(ais, src, tgt, src_type, tgt_type, handle="source"):
    return {
        "data": {"sourceType": src_type, "targetType": tgt_type, "isInIteration": False},
        "id": f"e-{nid(ais, src)}-{nid(ais, tgt)}",
        "source": nid(ais, src), "sourceHandle": handle,
        "target": nid(ais, tgt), "targetHandle": "target", "type": "custom"
    }

def mk_node(ais, num, x, y, ntype, title, desc, height=97, width=243, extra=None):
    nd = {
        "data": {"desc": desc, "selected": False, "title": title, "type": ntype},
        "height": height, "id": nid(ais, num),
        "position": {"x": x, "y": y},
        "positionAbsolute": {"x": x, "y": y},
        "selected": False, "sourcePosition": "right", "targetPosition": "left",
        "type": "custom", "width": width,
    }
    if extra:
        nd["data"].update(extra)
    return nd

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 共通テンプレート
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INJECTION_CODE_TPL = '''import re

def main({params}) -> dict:
    issues = []
{checks}
    injection_patterns = [
        r'(?i)ignore\\s+(previous|above|all)\\s+(instructions?|prompts?)',
        r'(?i)system\\s*prompt',
        r'(?i)you\\s+are\\s+now',
        r'(?i)forget\\s+(everything|all|your)',
        r'<script',
        r'javascript:',
        r'\\{{\\{{.*\\}}\\}}',
    ]
    combined = {combined}
    for pattern in injection_patterns:
        if re.search(pattern, combined):
            issues.append("不正な入力パターンが検出されました。正しい内容を入力してください。")
            break

    is_valid = "true" if len(issues) == 0 else "false"
    error_message = "" if is_valid == "true" else "\\n".join(issues)
    return {{'is_valid': is_valid, 'error_message': error_message}}'''

SENSITIVE_WORDS_CONFIG = {
    "enabled": True, "type": "keywords",
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
        "image": {"enabled": False, "number_limits": 3, "transfer_methods": ["local_file", "remote_url"]}
    },
    "opening_statement": "",
    "retriever_resource": {"enabled": False},
    "sensitive_word_avoidance": SENSITIVE_WORDS_CONFIG,
    "speech_to_text": {"enabled": False},
    "suggested_questions": [],
    "suggested_questions_after_answer": {"enabled": False},
    "text_to_speech": {"enabled": False, "language": "", "voice": ""}
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 自動ワークフロー構築
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_auto(cfg):
    """
    コンパクトな定義辞書から標準ワークフロー（Start→Code→IF-ELSE→LLM→TT→End）を自動構築する。

    cfg keys:
        num (int): AIS番号
        name (str): ワークフロー名
        file (str): 出力ファイル名
        desc (str): 説明
        icon (str): アイコン絵文字
        bg (str): アイコン背景色
        vars (list): 入力変数定義 [(name, type, options_or_max, required), ...]
            type: "paragraph" | "select" | "text"
            options_or_max: list (select) or int (max_length)
        main_var (str): メイン検証対象変数名
        min_len (int): 最小文字数
        sys (str): システムプロンプト
        out_header (str): 出力ヘッダータイトル
        disclaimer (str): 免責事項
        temp (float): LLM temperature
        mt (int): max_tokens
    """
    A = cfg["num"]

    # ── Start変数 ──
    start_vars = []
    for v in cfg["vars"]:
        vname, vtype = v[0], v[1]
        req = v[3] if len(v) > 3 else True
        sv = {"label": vname, "variable": vname, "required": req}
        if vtype == "paragraph":
            sv.update({"type": "paragraph", "max_length": v[2] if isinstance(v[2], int) else 999999, "options": []})
        elif vtype == "select":
            sv.update({"type": "select", "max_length": 48, "options": v[2]})
        elif vtype == "text":
            sv.update({"type": "text-input", "max_length": v[2] if isinstance(v[2], int) else 256, "options": []})
        start_vars.append(sv)

    # ── 入力検証コード ──
    para_vars = [v[0] for v in cfg["vars"] if v[1] == "paragraph"]
    if not para_vars:
        para_vars = [cfg["main_var"]]
    params_str = ", ".join(f"{v}: str" for v in para_vars)
    main_var = cfg["main_var"]
    min_len = cfg.get("min_len", 20)

    checks = f'    if len({main_var}.strip()) < {min_len}:\n        issues.append("入力が短すぎます（{min_len}文字以上必要）")'
    combined = " + ' ' + ".join(para_vars) if len(para_vars) > 1 else main_var

    code_text = INJECTION_CODE_TPL.format(params=params_str, checks=checks, combined=combined)
    code_vars = [{"value_selector": [nid(A, 1), v], "variable": v} for v in para_vars]

    # ── ユーザープロンプト ──
    user_parts = []
    for v in cfg["vars"]:
        vname = v[0]
        ref = "{{#" + nid(A, 1) + "." + vname + "#}}"
        if v[1] == "paragraph":
            user_parts.append(f"{vname}:\n{ref}")
        else:
            user_parts.append(f"{vname}: {ref}")
    user_prompt = "\n\n".join(user_parts)

    # ── 出力テンプレート ──
    meta_lines = []
    for v in cfg["vars"]:
        if v[1] != "paragraph":
            meta_lines.append(f"**{v[0]}**: {{{{ {v[0]} }}}}")
    meta_str = "\n".join(meta_lines)
    out_header = cfg.get("out_header", cfg["name"])
    disclaimer = cfg.get("disclaimer", "AIが生成した結果です。内容を確認してからご使用ください。")
    output_tpl = f"# {out_header}\n\n{meta_str}\n\n---\n\n{{{{ result }}}}\n\n---\n*{disclaimer}*"

    out_vars = [{"value_selector": [nid(A, 4), "text"], "variable": "result"}]
    for v in cfg["vars"]:
        if v[1] != "paragraph":
            out_vars.append({"value_selector": [nid(A, 1), v[0]], "variable": v[0]})

    # ── エラーテンプレート ──
    error_tpl = (
        f"## 入力エラー\n\n"
        f"{cfg['name']}の処理を開始できませんでした。\n\n"
        f"**エラー詳細**: {{{{ error_message }}}}\n\n"
        f"入力内容を修正して再度お試しください。"
    )

    # ── ノード構築 ──
    nodes = [
        mk_node(A, 1, 80, 282, "start", "開始", "入力パラメータを受け取る", height=149,
                extra={"variables": start_vars}),
        mk_node(A, 2, 380, 282, "code", "入力検証", "入力テキストの検証とインジェクション検出を行う",
                extra={"code_language": "python3", "code": code_text, "variables": code_vars,
                       "outputs": {"is_valid": {"type": "string"}, "error_message": {"type": "string"}}}),
        mk_node(A, 3, 680, 282, "if-else", "検証結果分岐", "入力検証結果で分岐する", height=125,
                extra={"cases": [{"case_id": "true", "logical_operator": "and",
                                  "conditions": [{"id": "cond_valid",
                                                  "variable_selector": [nid(A, 2), "is_valid"],
                                                  "comparison_operator": "is", "value": "true"}]}]}),
        mk_node(A, 4, 980, 182, "llm", "AI生成", cfg["desc"],
                extra={"context": {"enabled": False, "variable_selector": []},
                       "model": {"completion_params": {"frequency_penalty": 0, "max_tokens": cfg.get("mt", 4096),
                                                       "presence_penalty": 0, "temperature": cfg.get("temp", 0.3),
                                                       "top_p": 1},
                                 "mode": "chat", "name": "gpt-4o-mini", "provider": "openai"},
                       "prompt_template": [{"role": "system", "text": cfg["sys"]},
                                           {"role": "user", "text": user_prompt}],
                       "variables": [], "vision": {"enabled": False}}),
        mk_node(A, 5, 1280, 182, "template-transform", "出力整形", "生成結果にメタ情報を付与して整形する",
                extra={"template": output_tpl, "variables": out_vars}),
        mk_node(A, 6, 980, 432, "template-transform", "エラー応答", "入力検証エラー時のメッセージを整形する",
                extra={"template": error_tpl,
                       "variables": [{"value_selector": [nid(A, 2), "error_message"], "variable": "error_message"}]}),
        mk_node(A, 7, 1580, 282, "end", "終了", "結果またはエラーメッセージを出力する", height=89,
                extra={"outputs": [
                    {"value_selector": [nid(A, 5), "output"], "variable": "result"},
                    {"value_selector": [nid(A, 6), "output"], "variable": "error_message"},
                ]}),
    ]

    # ── エッジ構築 ──
    edges_list = [
        mk_edge(A, 1, 2, "start", "code"),
        mk_edge(A, 2, 3, "code", "if-else"),
        mk_edge(A, 3, 4, "if-else", "llm", "true"),
        mk_edge(A, 3, 6, "if-else", "template-transform", "false"),
        mk_edge(A, 4, 5, "llm", "template-transform"),
        mk_edge(A, 5, 7, "template-transform", "end"),
        mk_edge(A, 6, 7, "template-transform", "end"),
    ]

    # ── ワークフロー文書 ──
    return {
        "kind": "app",
        "version": "0.1.5",
        "app": {
            "description": cfg["desc"],
            "icon": cfg["icon"],
            "icon_background": cfg["bg"],
            "mode": "workflow",
            "name": f"AIS-{A}: {cfg['name']}",
            "use_icon_as_answer_icon": False,
        },
        "workflow": {
            "environment_variables": [],
            "conversation_variables": [],
            "features": dict(BASE_FEATURES),
            "graph": {
                "edges": edges_list,
                "nodes": nodes,
                "viewport": {"x": 0, "y": 0, "zoom": 1}
            }
        }
    }


def generate_batch(workflows):
    """ワークフロー定義リストからYAMLファイルを一括生成する"""
    count = 0
    for cfg in workflows:
        doc = build_auto(cfg)
        doc = convert_multiline(doc)
        filepath = os.path.join(OUTPUT_DIR, cfg["file"])
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(doc, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=200)
        print(f"  ✓ {cfg['file']}")
        count += 1
    return count
