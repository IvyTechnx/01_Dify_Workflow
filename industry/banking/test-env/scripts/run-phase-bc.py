#!/usr/bin/env python3
"""
Phase B + C テスト実行スクリプト

Phase B: ナレッジベース依存テスト（TC-01〜05, TC-13, TC-17）
  → KBドキュメントの内容検証 + ワークフロー設定検証
  （実際の KR + LLM は Dify 上で実行。ここではソース文書の充足性を検証）

Phase C: モックAPI依存テスト（TC-23〜26, TC-36〜40）
  → モックサーバーに実HTTP通信し、Code ノードを忠実に再現
  （TC-19〜22 は run-tc19-22.py で実施済み）

使い方:
  1. モックサーバーを起動: cd mock-server && python app.py
  2. 本スクリプトを実行: python scripts/run-phase-bc.py
"""

import json
import os
import sys
import urllib.parse
import urllib.request
import re

# ============================================================
# 設定
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, 'knowledge-bases')
WORKFLOW_DIR = os.path.join(BASE_DIR, '..')  # industry/banking/
MOCK_BASE = 'http://localhost:5001'

results = []

# ============================================================
# ユーティリティ
# ============================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def record(tc_id: str, title: str, passed: bool, detail: str = ''):
    status = f'{Colors.GREEN}PASS{Colors.RESET}' if passed else f'{Colors.RED}FAIL{Colors.RESET}'
    results.append((tc_id, title, passed, detail))
    print(f'  [{status}] {tc_id}: {title}')
    if detail and not passed:
        for line in detail.split('\n'):
            print(f'         {line}')


def load_text(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def load_yaml_text(filename: str) -> str:
    """ワークフローYAMLをテキストとして読み込み（YAML解析不要な検証用）"""
    path = os.path.join(WORKFLOW_DIR, filename)
    return load_text(path)


def http_get(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))


def http_post(url: str, data: dict) -> dict:
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))


# ============================================================
# Phase B: ナレッジベース依存テスト
# ============================================================

def run_phase_b():
    print(f'\n{Colors.BOLD}{Colors.CYAN}══════════════════════════════════════════════════{Colors.RESET}')
    print(f'{Colors.BOLD}{Colors.CYAN}  Phase B: ナレッジベース依存テスト{Colors.RESET}')
    print(f'{Colors.BOLD}{Colors.CYAN}══════════════════════════════════════════════════{Colors.RESET}')

    compliance_kb = load_text(os.path.join(KB_DIR, 'compliance-kb.md'))
    account_kb = load_text(os.path.join(KB_DIR, 'account-kb.md'))
    bnk01_yaml = load_yaml_text('bnk-01-compliance-search.yml')
    bnk03_yaml = load_yaml_text('bnk-03-customer-inquiry.yml')

    # ----------------------------------------------------------
    # TC-01: 基本的な規程検索
    # question: 反社会的勢力との取引に関する社内規程
    # 期待: KB に反社規程あり、規程名・条項番号を含む
    # ----------------------------------------------------------
    print(f'\n{Colors.BOLD}--- BNK-01: コンプライアンス規程・法令検索 ---{Colors.RESET}')

    checks_01 = [
        '反社会的勢力' in compliance_kb,
        '第1条' in compliance_kb,
        '第2条' in compliance_kb,
        '取引遮断' in compliance_kb or '取引遮断規程' in compliance_kb,
    ]
    detail_01 = (
        f'反社会的勢力: {"○" if checks_01[0] else "×"}, '
        f'第1条: {"○" if checks_01[1] else "×"}, '
        f'第2条: {"○" if checks_01[2] else "×"}, '
        f'取引遮断: {"○" if checks_01[3] else "×"}'
    )
    record('TC-01', '基本的な規程検索 — KB内容充足性', all(checks_01), detail_01)

    # ----------------------------------------------------------
    # TC-02: 具体的な条文参照（AML金額基準）
    # 期待: 200万円超の現金取引、10万円超の現金送金、犯収法
    # ----------------------------------------------------------
    checks_02 = [
        '200万円' in compliance_kb,
        '10万円' in compliance_kb,
        '犯収法' in compliance_kb or '犯罪収益移転防止' in compliance_kb,
        '取引時確認' in compliance_kb,
        '第11条' in compliance_kb,
    ]
    detail_02 = (
        f'200万円: {"○" if checks_02[0] else "×"}, '
        f'10万円: {"○" if checks_02[1] else "×"}, '
        f'犯収法: {"○" if checks_02[2] else "×"}, '
        f'取引時確認: {"○" if checks_02[3] else "×"}, '
        f'第11条: {"○" if checks_02[4] else "×"}'
    )
    record('TC-02', '具体的な条文参照（AML金額基準） — KB内容充足性', all(checks_02), detail_02)

    # ----------------------------------------------------------
    # TC-03: 曖昧な質問 → 内線5001案内
    # 期待: KB に内線5001あり + LLMプロンプトに案内ルールあり
    # ----------------------------------------------------------
    checks_03 = [
        '内線5001' in compliance_kb or '内線 5001' in compliance_kb,
        'コンプライアンス部' in compliance_kb,
        '内線: 5001' in bnk01_yaml or '内線5001' in bnk01_yaml,
        '該当情報がない場合' in bnk01_yaml,
    ]
    detail_03 = (
        f'KB内線5001: {"○" if checks_03[0] else "×"}, '
        f'KBコンプライアンス部: {"○" if checks_03[1] else "×"}, '
        f'YAMLプロンプト内線: {"○" if checks_03[2] else "×"}, '
        f'該当なし案内ルール: {"○" if checks_03[3] else "×"}'
    )
    record('TC-03', '曖昧な質問 → 内線5001案内 — KB+プロンプト検証', all(checks_03), detail_03)

    # ----------------------------------------------------------
    # TC-04: ナレッジベースに該当なし（食堂メニュー）
    # 期待: KB に食堂・メニュー情報が存在しない
    # ----------------------------------------------------------
    checks_04 = [
        '食堂' not in compliance_kb,
        'メニュー' not in compliance_kb,
        'ランチ' not in compliance_kb,
    ]
    detail_04 = (
        f'食堂なし: {"○" if checks_04[0] else "×"}, '
        f'メニューなし: {"○" if checks_04[1] else "×"}, '
        f'ランチなし: {"○" if checks_04[2] else "×"}'
    )
    record('TC-04', 'KB該当なし（食堂メニュー） — 非収録確認', all(checks_04), detail_04)

    # ----------------------------------------------------------
    # TC-05: 安全性 — 禁止キーワード「爆弾」
    # 期待: sensitive_word_avoidance に「爆弾」+プリセット応答設定
    # ----------------------------------------------------------
    checks_05 = [
        'sensitive_word_avoidance' in bnk01_yaml,
        '爆弾' in bnk01_yaml,
        'enabled: true' in bnk01_yaml,
        'その内容にはお答えできません' in bnk01_yaml,
    ]
    detail_05 = (
        f'SWA設定: {"○" if checks_05[0] else "×"}, '
        f'爆弾キーワード: {"○" if checks_05[1] else "×"}, '
        f'有効化: {"○" if checks_05[2] else "×"}, '
        f'プリセット応答: {"○" if checks_05[3] else "×"}'
    )
    record('TC-05', '安全性 — 禁止キーワード「爆弾」 — SWA設定検証', all(checks_05), detail_05)

    # ----------------------------------------------------------
    # TC-13: 口座分岐 — 口座KB内容充足性
    # question: 普通預金口座の開設に必要な書類
    # 期待: KB に開設手続き・必要書類あり
    # ----------------------------------------------------------
    print(f'\n{Colors.BOLD}--- BNK-03: 顧客問い合わせ対応チャット ---{Colors.RESET}')

    checks_13 = [
        '普通預金口座の開設' in account_kb or '普通預金口座' in account_kb,
        '必要書類' in account_kb,
        '本人確認書類' in account_kb,
        '運転免許証' in account_kb,
        'マイナンバーカード' in account_kb,
        '届出印' in account_kb,
    ]
    detail_13 = (
        f'普通預金: {"○" if checks_13[0] else "×"}, '
        f'必要書類: {"○" if checks_13[1] else "×"}, '
        f'本人確認: {"○" if checks_13[2] else "×"}, '
        f'免許証: {"○" if checks_13[3] else "×"}, '
        f'マイナンバー: {"○" if checks_13[4] else "×"}, '
        f'届出印: {"○" if checks_13[5] else "×"}'
    )
    record('TC-13', '口座分岐 — 口座KB内容充足性', all(checks_13), detail_13)

    # QC 分岐設定検証（口座分類の instruction）
    checks_13_qc = [
        'class_account' in bnk03_yaml,
        '口座開設' in bnk03_yaml,
        'account-kb-placeholder' in bnk03_yaml,
    ]
    detail_13_qc = (
        f'class_account: {"○" if checks_13_qc[0] else "×"}, '
        f'口座開設分類: {"○" if checks_13_qc[1] else "×"}, '
        f'KBプレースホルダ: {"○" if checks_13_qc[2] else "×"}'
    )
    record('TC-13+', '口座分岐 — QC+KR設定検証', all(checks_13_qc), detail_13_qc)

    # ----------------------------------------------------------
    # TC-17: 会話履歴テスト（マルチターン）
    # 現行DSL: workflow モードのため memory 設定なし
    # advanced-chat モードに変更する場合は memory を追加すること
    # ----------------------------------------------------------
    is_advanced_chat = 'advanced-chat' in bnk03_yaml
    if is_advanced_chat:
        checks_17 = [
            'memory:' in bnk03_yaml,
            'window:' in bnk03_yaml,
            'size: 10' in bnk03_yaml,
            True,
        ]
        detail_17 = (
            f'memory設定: {"○" if checks_17[0] else "×"}, '
            f'window設定: {"○" if checks_17[1] else "×"}, '
            f'size=10: {"○" if checks_17[2] else "×"}, '
            f'advanced-chat: ○'
        )
    else:
        checks_17 = [True]
        detail_17 = 'workflowモード — memory設定不要(SKIP)'
    record('TC-17', '会話履歴テスト — memory.window設定検証', all(checks_17), detail_17)


# ============================================================
# Phase C: モックAPI依存テスト — BNK-05 支店実績レポート
# ============================================================

# --- BNK-05 Code ノード 30500000000002（支店配列化）再現 ---
def bnk05_code_split(branch_list: str, report_period: str) -> dict:
    items = [b.strip() for b in branch_list.split(',') if b.strip()]
    report_period_enc = urllib.parse.quote(report_period, safe='')
    return {'items': items, 'report_period_enc': report_period_enc}


# --- BNK-05 Iteration: HTTP GET per branch ---
def bnk05_iteration_http(items: list, report_period_enc: str) -> list:
    """各支店の実績データをモックAPIから取得"""
    api_results = []
    for branch_code in items:
        url = f'{MOCK_BASE}/branch-performance?branch={branch_code}&period={report_period_enc}'
        try:
            resp = http_get(url)
            api_results.append(json.dumps(resp, ensure_ascii=False))
        except Exception as e:
            api_results.append(json.dumps({'error': str(e)}, ensure_ascii=False))
    return api_results


# --- BNK-05 Code ノード 30500000000005（結果集約）再現 ---
def bnk05_code_aggregate(api_results: list) -> dict:
    summary_lines = []
    for i, result in enumerate(api_results):
        try:
            data = json.loads(result) if isinstance(result, str) else result
            branch = data.get('branch_code', f'支店{i+1}')
            branch_name = data.get('branch_name', branch)
            deposits = data.get('deposits_billion', 'N/A')
            loans = data.get('loans_billion', 'N/A')
            profit = data.get('profit_million', 'N/A')
            new_accounts = data.get('new_accounts', 'N/A')
            summary_lines.append(
                f"支店: {branch_name}({branch}), "
                f"預金残高: {deposits}億円, "
                f"貸出残高: {loans}億円, "
                f"利益: {profit}百万円, "
                f"新規口座: {new_accounts}件"
            )
        except Exception:
            summary_lines.append(f"支店{i+1}: データ取得エラー")
    summary = '\n'.join(summary_lines)
    return {'summary': summary}


def run_bnk05_workflow(branch_list: str, report_period: str) -> dict:
    """BNK-05 ワークフロー全体を再現（LLM除く）"""
    # Step 1: Code (split + URL encode)
    split_result = bnk05_code_split(branch_list, report_period)

    # Step 2: Iteration (HTTP GET per branch)
    api_results = bnk05_iteration_http(
        split_result['items'],
        split_result['report_period_enc'],
    )

    # Step 3: Code (aggregate)
    aggregate_result = bnk05_code_aggregate(api_results)

    return {
        'split_result': split_result,
        'api_results': api_results,
        'summary': aggregate_result['summary'],
    }


# ============================================================
# Phase C: モックAPI依存テスト — BNK-08 為替レート照会
# ============================================================

# --- BNK-08 Code ノード 30800000000002（URLエンコード）再現 ---
def bnk08_code_url_encode(currency_pair: str) -> dict:
    pair_enc = urllib.parse.quote(currency_pair, safe='')
    return {'currency_pair_enc': pair_enc}


# --- BNK-08 HTTP GET ---
def bnk08_http_get(pair_enc: str) -> str:
    url = f'{MOCK_BASE}/fx-rate?pair={pair_enc}'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode('utf-8')


# --- BNK-08 Code ノード 30800000000004（レート解析）再現 ---
def bnk08_code_parse_rate(api_response: str) -> dict:
    try:
        data = json.loads(api_response) if isinstance(api_response, str) else api_response
        pair = data.get('pair', 'N/A')
        bid = data.get('bid', 0)
        ask = data.get('ask', 0)
        mid = (bid + ask) / 2 if bid and ask else 0
        spread = ask - bid if bid and ask else 0
        change_24h = data.get('change_24h_percent', 0)
        high_24h = data.get('high_24h', 0)
        low_24h = data.get('low_24h', 0)
        timestamp = data.get('timestamp', 'N/A')
        summary = (
            f"通貨ペア: {pair}\n"
            f"Bid(売値): {bid:.2f}\n"
            f"Ask(買値): {ask:.2f}\n"
            f"仲値: {mid:.2f}\n"
            f"スプレッド: {spread:.2f}\n"
            f"24H変動率: {change_24h:+.2f}%\n"
            f"24H高値: {high_24h:.2f}\n"
            f"24H安値: {low_24h:.2f}\n"
            f"取得日時: {timestamp}"
        )
        return {'summary': summary}
    except Exception:
        return {'summary': 'レートデータ取得エラー'}


def run_bnk08_workflow(currency_pair: str, customer_purpose: str) -> dict:
    """BNK-08 ワークフロー全体を再現（LLM除く）"""
    # Step 1: Code (URL encode)
    enc_result = bnk08_code_url_encode(currency_pair)

    # Step 2: HTTP GET
    raw_response = bnk08_http_get(enc_result['currency_pair_enc'])

    # Step 3: Code (parse rate)
    parse_result = bnk08_code_parse_rate(raw_response)

    return {
        'pair_enc': enc_result['currency_pair_enc'],
        'raw_response': raw_response,
        'summary': parse_result['summary'],
    }


# ============================================================
# Phase C テスト実行
# ============================================================

def run_phase_c():
    print(f'\n{Colors.BOLD}{Colors.CYAN}══════════════════════════════════════════════════{Colors.RESET}')
    print(f'{Colors.BOLD}{Colors.CYAN}  Phase C: モックAPI依存テスト{Colors.RESET}')
    print(f'{Colors.BOLD}{Colors.CYAN}══════════════════════════════════════════════════{Colors.RESET}')

    # 疎通確認
    print(f'\n{Colors.BOLD}--- モックサーバー疎通確認 ---{Colors.RESET}')
    try:
        health = http_get(f'{MOCK_BASE}/health')
        assert health.get('status') == 'ok'
        print(f'  {Colors.GREEN}✓ モックサーバー応答OK{Colors.RESET}')
    except Exception as e:
        print(f'  {Colors.RED}✗ モックサーバーに接続できません: {e}{Colors.RESET}')
        print(f'  → cd mock-server && python app.py でサーバーを起動してください')
        # Phase C テストをスキップ
        for tc_id in ['TC-23', 'TC-24', 'TC-25', 'TC-26',
                       'TC-36', 'TC-37', 'TC-38', 'TC-39', 'TC-40']:
            record(tc_id, 'SKIP（モックサーバー未起動）', False, str(e))
        return

    # ==============================================================
    # BNK-05: 支店実績経営分析レポート（TC-23〜26）
    # ==============================================================
    print(f'\n{Colors.BOLD}--- BNK-05: 支店実績経営分析レポート ---{Colors.RESET}')

    # ----------------------------------------------------------
    # TC-23: 複数支店（標準ケース）
    # ----------------------------------------------------------
    r23 = run_bnk05_workflow('BR-001, BR-002, BR-003, BR-004, BR-005', '2024Q3')
    checks_23 = [
        len(r23['split_result']['items']) == 5,
        '東京中央支店' in r23['summary'],
        '大阪梅田支店' in r23['summary'],
        '名古屋駅前支店' in r23['summary'],
        '横浜みなとみらい支店' in r23['summary'],
        '札幌大通支店' in r23['summary'],
        'データ取得エラー' not in r23['summary'],
        r23['summary'].count('預金残高:') == 5,
    ]
    detail_23 = (
        f'配列数={len(r23["split_result"]["items"])}, '
        f'全5支店名含む: {"○" if all(checks_23[1:6]) else "×"}, '
        f'エラーなし: {"○" if checks_23[6] else "×"}'
    )
    record('TC-23', '複数支店（5支店標準ケース）', all(checks_23), detail_23)

    # ----------------------------------------------------------
    # TC-24: 単一支店
    # ----------------------------------------------------------
    r24 = run_bnk05_workflow('BR-001', '2024Q4')
    checks_24 = [
        len(r24['split_result']['items']) == 1,
        '東京中央支店' in r24['summary'],
        r24['summary'].count('預金残高:') == 1,
        'データ取得エラー' not in r24['summary'],
    ]
    detail_24 = (
        f'配列数={len(r24["split_result"]["items"])}, '
        f'period_enc={r24["split_result"]["report_period_enc"]}'
    )
    record('TC-24', '単一支店', all(checks_24), detail_24)

    # ----------------------------------------------------------
    # TC-25: 多数支店（20支店全部）
    # ----------------------------------------------------------
    all_branches = ', '.join([f'BR-{i:03d}' for i in range(1, 21)])
    r25 = run_bnk05_workflow(all_branches, '2024年度上期')
    checks_25 = [
        len(r25['split_result']['items']) == 20,
        r25['split_result']['report_period_enc'] == '2024%E5%B9%B4%E5%BA%A6%E4%B8%8A%E6%9C%9F',
        r25['summary'].count('預金残高:') == 20,
        '東京中央支店' in r25['summary'],
        '鹿児島天文館支店' in r25['summary'],
        'データ取得エラー' not in r25['summary'],
    ]
    detail_25 = (
        f'配列数={len(r25["split_result"]["items"])}, '
        f'period_enc={r25["split_result"]["report_period_enc"]}, '
        f'集約行数={r25["summary"].count("預金残高:")}'
    )
    record('TC-25', '多数支店（20支店一括）', all(checks_25), detail_25)

    # ----------------------------------------------------------
    # TC-26: スペースや全角を含む支店リスト
    # ----------------------------------------------------------
    r26 = run_bnk05_workflow('BR-001,\u3000BR-002 , BR-003', '2024Q3')
    checks_26 = [
        len(r26['split_result']['items']) == 3,
        # strip() で全角スペースも除去されているか
        r26['split_result']['items'][1] == 'BR-002',
        '東京中央支店' in r26['summary'],
        '大阪梅田支店' in r26['summary'],
        '名古屋駅前支店' in r26['summary'],
        'データ取得エラー' not in r26['summary'],
    ]
    # Python の str.strip() は全角スペース(\u3000)も除去する
    detail_26 = (
        f'配列数={len(r26["split_result"]["items"])}, '
        f'items={r26["split_result"]["items"]}, '
        f'全角strip: {"○" if checks_26[1] else "×"}'
    )
    record('TC-26', 'スペース・全角を含む支店リスト', all(checks_26), detail_26)

    # ==============================================================
    # BNK-08: 外国為替レート照会（TC-36〜40）
    # ==============================================================
    print(f'\n{Colors.BOLD}--- BNK-08: 外国為替レート照会 ---{Colors.RESET}')

    # ----------------------------------------------------------
    # TC-36: USD/JPY + 海外送金
    # ----------------------------------------------------------
    r36 = run_bnk08_workflow('USD/JPY', '海外送金')
    checks_36 = [
        'USD/JPY' in r36['summary'],
        'Bid(売値): 149.85' in r36['summary'],
        'Ask(買値): 149.88' in r36['summary'],
        # mid = (149.85 + 149.88) / 2 = 149.865
        '仲値: 149.86' in r36['summary'] or '仲値: 149.87' in r36['summary'],
        # spread = 149.88 - 149.85 = 0.03
        'スプレッド: 0.03' in r36['summary'],
        '24H変動率: +0.32%' in r36['summary'],
        'レートデータ取得エラー' not in r36['summary'],
    ]
    # 仲値の正確値確認
    expected_mid_36 = (149.85 + 149.88) / 2  # 149.865
    actual_mid_line = [l for l in r36['summary'].split('\n') if '仲値' in l]
    detail_36 = (
        f'pair_enc={r36["pair_enc"]}, '
        f'mid計算={expected_mid_36:.2f}, '
        f'spread=0.03, '
        f'変動率=+0.32%'
    )
    record('TC-36', 'USD/JPY + 海外送金', all(checks_36), detail_36)

    # ----------------------------------------------------------
    # TC-37: EUR/JPY + 外貨預金
    # ----------------------------------------------------------
    r37 = run_bnk08_workflow('EUR/JPY', '外貨預金')
    expected_mid_37 = (162.45 + 162.50) / 2  # 162.475
    expected_spread_37 = 162.50 - 162.45  # 0.05
    checks_37 = [
        'EUR/JPY' in r37['summary'],
        'Bid(売値): 162.45' in r37['summary'],
        'Ask(買値): 162.50' in r37['summary'],
        f'仲値: {expected_mid_37:.2f}' in r37['summary'],
        f'スプレッド: {expected_spread_37:.2f}' in r37['summary'],
        '24H変動率: -0.18%' in r37['summary'],
        'レートデータ取得エラー' not in r37['summary'],
    ]
    detail_37 = (
        f'mid={expected_mid_37:.2f}, '
        f'spread={expected_spread_37:.2f}, '
        f'変動率=-0.18%'
    )
    record('TC-37', 'EUR/JPY + 外貨預金', all(checks_37), detail_37)

    # ----------------------------------------------------------
    # TC-38: GBP/JPY + 輸出入決済
    # ----------------------------------------------------------
    r38 = run_bnk08_workflow('GBP/JPY', '輸出入決済')
    expected_mid_38 = (189.32 + 189.40) / 2  # 189.36
    expected_spread_38 = 189.40 - 189.32  # 0.08
    checks_38 = [
        'GBP/JPY' in r38['summary'],
        'Bid(売値): 189.32' in r38['summary'],
        'Ask(買値): 189.40' in r38['summary'],
        f'仲値: {expected_mid_38:.2f}' in r38['summary'],
        f'スプレッド: {expected_spread_38:.2f}' in r38['summary'],
        '24H変動率: +0.45%' in r38['summary'],
        'レートデータ取得エラー' not in r38['summary'],
    ]
    detail_38 = (
        f'mid={expected_mid_38:.2f}, '
        f'spread={expected_spread_38:.2f}, '
        f'変動率=+0.45%'
    )
    record('TC-38', 'GBP/JPY + 輸出入決済', all(checks_38), detail_38)

    # ----------------------------------------------------------
    # TC-39: AUD/JPY + 旅行
    # ----------------------------------------------------------
    r39 = run_bnk08_workflow('AUD/JPY', '旅行')
    expected_mid_39 = (97.65 + 97.70) / 2  # 97.675
    expected_spread_39 = 97.70 - 97.65  # 0.05
    checks_39 = [
        'AUD/JPY' in r39['summary'],
        'Bid(売値): 97.65' in r39['summary'],
        'Ask(買値): 97.70' in r39['summary'],
        f'仲値: {expected_mid_39:.2f}' in r39['summary'],
        f'スプレッド: {expected_spread_39:.2f}' in r39['summary'],
        '24H変動率: -0.22%' in r39['summary'],
        'レートデータ取得エラー' not in r39['summary'],
    ]
    detail_39 = (
        f'mid={expected_mid_39:.2f}, '
        f'spread={expected_spread_39:.2f}, '
        f'変動率=-0.22%'
    )
    record('TC-39', 'AUD/JPY + 旅行', all(checks_39), detail_39)

    # ----------------------------------------------------------
    # TC-40: THB/JPY（未対応通貨ペア）
    # 期待: API は 200 + error フィールド → Code ノードで耐性テスト
    # Code ノードは bid=0, ask=0 → data.get() でデフォルト値適用
    # → pair='N/A', 0.00 のサマリを生成（例外にはならない）
    # ----------------------------------------------------------
    r40 = run_bnk08_workflow('THB/JPY', '海外送金')
    raw_40 = json.loads(r40['raw_response'])
    checks_40 = [
        'error' in raw_40,
        'Unsupported currency pair' in raw_40.get('error', ''),
        # Code ノードはクラッシュせず、N/A + 0.00 で処理を継続する
        '通貨ペア: N/A' in r40['summary'] or 'レートデータ取得エラー' in r40['summary'],
        # 仲値・スプレッドが 0.00（bid=ask=0 のため）
        '仲値: 0.00' in r40['summary'] or 'レートデータ取得エラー' in r40['summary'],
    ]
    detail_40 = (
        f'APIエラーフィールド: {"○" if checks_40[0] else "×"}, '
        f'Unsupported: {"○" if checks_40[1] else "×"}, '
        f'Codeノード耐性(クラッシュなし): {"○" if checks_40[2] else "×"}, '
        f'デフォルト値適用: {"○" if checks_40[3] else "×"}'
    )
    record('TC-40', 'THB/JPY（未対応通貨ペア） — Code耐性テスト', all(checks_40), detail_40)


# ============================================================
# メイン
# ============================================================

def main():
    print(f'{Colors.BOLD}╔══════════════════════════════════════════════════╗{Colors.RESET}')
    print(f'{Colors.BOLD}║  Banking ワークフロー Phase B + C テスト          ║{Colors.RESET}')
    print(f'{Colors.BOLD}╚══════════════════════════════════════════════════╝{Colors.RESET}')

    run_phase_b()
    run_phase_c()

    # サマリ
    total = len(results)
    passed = sum(1 for r in results if r[2])
    failed = total - passed

    print(f'\n{Colors.BOLD}══════════════════════════════════════════════════{Colors.RESET}')
    print(f'{Colors.BOLD}  結果サマリ{Colors.RESET}')
    print(f'{Colors.BOLD}══════════════════════════════════════════════════{Colors.RESET}')

    # Phase B
    phase_b_results = [r for r in results if r[0] in
                       ['TC-01', 'TC-02', 'TC-03', 'TC-04', 'TC-05',
                        'TC-13', 'TC-13+', 'TC-17']]
    phase_b_pass = sum(1 for r in phase_b_results if r[2])
    phase_b_total = len(phase_b_results)

    # Phase C
    phase_c_results = [r for r in results if r[0] in
                       ['TC-23', 'TC-24', 'TC-25', 'TC-26',
                        'TC-36', 'TC-37', 'TC-38', 'TC-39', 'TC-40']]
    phase_c_pass = sum(1 for r in phase_c_results if r[2])
    phase_c_total = len(phase_c_results)

    print(f'\n  Phase B (KB依存): {phase_b_pass}/{phase_b_total}')
    print(f'  Phase C (API依存): {phase_c_pass}/{phase_c_total}')
    print(f'  ─────────────────────')
    print(f'  合計: {passed}/{total}')

    if failed > 0:
        print(f'\n  {Colors.RED}FAILED テスト:{Colors.RESET}')
        for tc_id, title, p, detail in results:
            if not p:
                print(f'    {tc_id}: {title}')
                if detail:
                    print(f'      → {detail}')

    color = Colors.GREEN if failed == 0 else Colors.RED
    print(f'\n{color}{Colors.BOLD}  {"ALL PASSED" if failed == 0 else f"{failed} FAILED"}{Colors.RESET}\n')

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
