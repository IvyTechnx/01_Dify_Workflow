#!/usr/bin/env python3
"""Dify DSL YAML生成コアエンジン"""
import yaml, os

BASE = "/Users/ivytech/Claude/01_Dify_Workflow/catalog"

FEATURES = {
    'file_upload': {'image': {'enabled': False, 'number_limits': 3, 'transfer_methods': ['local_file', 'remote_url']}},
    'opening_statement': '',
    'retriever_resource': {'enabled': False},
    'sensitive_word_avoidance': {
        'enabled': True, 'type': 'keywords',
        'config': {
            'keywords': "爆弾\n殺害\n違法薬物\nハッキング手法",
            'inputs_config': {'enabled': True, 'preset_response': 'その内容にはお答えできません。別の質問をお願いします。'},
            'outputs_config': {'enabled': True, 'preset_response': '適切な回答を生成できませんでした。質問を変えてください。'}
        }
    },
    'speech_to_text': {'enabled': False},
    'suggested_questions': [],
    'suggested_questions_after_answer': {'enabled': False},
    'text_to_speech': {'enabled': False, 'language': '', 'voice': ''}
}

def make_var(name, vtype, required=True, options=None, max_length=None):
    v = {'label': name, 'variable': name, 'required': required, 'type': vtype, 'options': options or []}
    if vtype == 'paragraph':
        v['max_length'] = max_length or 999999
    elif vtype == 'text-input':
        v['max_length'] = max_length or 200
    elif vtype == 'select':
        v['max_length'] = 48
    return v

def nid(wf_num, seq):
    return str(wf_num * 100000000 + seq)

def make_edge(src, tgt, src_type, tgt_type, src_handle='source'):
    return {
        'data': {'sourceType': src_type, 'targetType': tgt_type, 'isInIteration': False},
        'id': f'e-{src}-{tgt}', 'source': src, 'sourceHandle': src_handle,
        'target': tgt, 'targetHandle': 'target', 'type': 'custom'
    }

def make_node(node_id, data, x, y, h=97, w=243):
    return {
        'data': data, 'height': h, 'id': node_id, 'type': 'custom',
        'position': {'x': x, 'y': y}, 'positionAbsolute': {'x': x, 'y': y},
        'selected': False, 'sourcePosition': 'right', 'targetPosition': 'left', 'width': w
    }

def validation_code(main_var):
    return f'''import re

def main({main_var}: str) -> dict:
    text = {main_var}.strip()
    if len(text) < 10:
        return {{'is_valid': 'false', 'error_message': '入力が短すぎます（10文字以上必要）'}}
    injection_patterns = [
        r'(?i)ignore\\s+(previous|above|all)\\s+(instructions?|prompts?)',
        r'(?i)system\\s*prompt', r'(?i)you\\s+are\\s+now',
        r'(?i)forget\\s+(everything|all|your)',
        r'<script', r'javascript:', r'\\{{\\{{.*\\}}\\}}',
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text):
            return {{'is_valid': 'false', 'error_message': '不正な入力パターンが検出されました。'}}
    return {{'is_valid': 'true', 'error_message': ''}}'''

def gen_workflow(wf_num, slug, name, icon, icon_bg, desc, variables, main_var, system_prompt, user_prompt_template, output_title):
    ids = [nid(wf_num, i) for i in range(1, 8)]
    # ids: 0=start, 1=code, 2=if-else, 3=llm, 4=template, 5=error-template, 6=end

    edges = [
        make_edge(ids[0], ids[1], 'start', 'code'),
        make_edge(ids[1], ids[2], 'code', 'if-else'),
        make_edge(ids[2], ids[3], 'if-else', 'llm', 'true'),
        make_edge(ids[2], ids[5], 'if-else', 'template-transform', 'false'),
        make_edge(ids[3], ids[4], 'llm', 'template-transform'),
        make_edge(ids[4], ids[6], 'template-transform', 'end'),
        make_edge(ids[5], ids[6], 'template-transform', 'end'),
    ]

    nodes = [
        # Start
        make_node(ids[0], {
            'desc': '入力パラメータを受け取る', 'selected': False, 'title': '開始',
            'type': 'start', 'variables': variables
        }, 80, 282, 149),
        # Code validation
        make_node(ids[1], {
            'desc': '入力テキストの検証とインジェクション検出を行う', 'selected': False,
            'title': '入力検証', 'type': 'code', 'code_language': 'python3',
            'code': validation_code(main_var),
            'variables': [{'value_selector': [ids[0], main_var], 'variable': main_var}],
            'outputs': {'is_valid': {'type': 'string'}, 'error_message': {'type': 'string'}}
        }, 380, 282),
        # IF-ELSE
        make_node(ids[2], {
            'desc': '入力検証結果で分岐する', 'selected': False, 'title': '検証結果分岐',
            'type': 'if-else',
            'cases': [{'case_id': 'true', 'logical_operator': 'and', 'conditions': [
                {'id': 'cond_valid', 'variable_selector': [ids[1], 'is_valid'],
                 'comparison_operator': 'is', 'value': 'true'}
            ]}]
        }, 680, 282, 125),
        # LLM
        make_node(ids[3], {
            'desc': desc, 'selected': False, 'title': 'AI生成', 'type': 'llm',
            'context': {'enabled': False, 'variable_selector': []},
            'model': {
                'completion_params': {'frequency_penalty': 0, 'max_tokens': 4096,
                                      'presence_penalty': 0, 'temperature': 0.5, 'top_p': 1},
                'mode': 'chat', 'name': 'gpt-4o-mini', 'provider': 'openai'
            },
            'prompt_template': [
                {'role': 'system', 'text': system_prompt},
                {'role': 'user', 'text': user_prompt_template}
            ],
            'variables': [], 'vision': {'enabled': False}
        }, 980, 182),
        # Template output
        make_node(ids[4], {
            'desc': '生成結果にメタ情報を付与して整形する', 'selected': False,
            'title': '出力整形', 'type': 'template-transform',
            'template': f'# {output_title}\n\n---\n\n{{{{ result }}}}\n\n---\n*AIが生成したドラフトです。専門家の確認を行ってからご使用ください。*',
            'variables': [{'value_selector': [ids[3], 'text'], 'variable': 'result'}]
        }, 1280, 182),
        # Error template
        make_node(ids[5], {
            'desc': '入力検証エラー時のメッセージを整形する', 'selected': False,
            'title': 'エラー応答', 'type': 'template-transform',
            'template': '## 入力エラー\n\n処理を開始できませんでした。\n\n**エラー詳細**: {{ error_message }}\n\n入力内容を修正して再度お試しください。',
            'variables': [{'value_selector': [ids[1], 'error_message'], 'variable': 'error_message'}]
        }, 980, 432),
        # End
        make_node(ids[6], {
            'desc': '結果またはエラーメッセージを出力する', 'selected': False,
            'title': '終了', 'type': 'end',
            'outputs': [
                {'value_selector': [ids[4], 'output'], 'variable': 'result'},
                {'value_selector': [ids[5], 'output'], 'variable': 'error_message'}
            ]
        }, 1580, 282, 89),
    ]

    dsl = {
        'kind': 'app', 'version': '0.1.5',
        'app': {
            'description': desc, 'icon': icon, 'icon_background': icon_bg,
            'mode': 'workflow', 'name': f'AIS-{wf_num}: {name}',
            'use_icon_as_answer_icon': False
        },
        'workflow': {
            'environment_variables': [], 'conversation_variables': [],
            'features': FEATURES,
            'graph': {'edges': edges, 'nodes': nodes, 'viewport': {'x': 0, 'y': 0, 'zoom': 1}}
        }
    }

    return dsl

def save_workflow(category, wf_num, slug, dsl):
    path = os.path.join(BASE, category, f'ais-{wf_num}-{slug}.yml')
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(dsl, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=200)
    print(f"  Created: {path}")
