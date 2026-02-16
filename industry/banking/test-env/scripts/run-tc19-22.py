"""
TC-19〜22: BNK-04 不正取引アラート ワークフロー シミュレーション

ワークフローのノードチェーンを忠実に再現し、モックAPIに実リクエストを送信する。
LLM ノード（30400000000005）はスタブで代替する。

フロー:
  Start → URLエンコード(Code) → 取引データ取得(HTTP) → データ整形(Code)
  → 不正分析(LLM※スタブ) → リスク判定抽出(Code) → エスカレーション判定(IF/ELSE)
  → [TRUE]  JSON構築(Code) → エスカレーション通知(HTTP) → 結果集約 → End
  → [FALSE] 通常処理(Template) → 結果集約 → End
"""

import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error

BASE_URL = 'http://localhost:5001'

# ─── カラー出力 ───

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

# ─── テストケース定義 ───

TEST_CASES = [
    {
        'id': 'TC-19',
        'title': 'HIGH リスク → エスカレーション',
        'transaction_id': 'TXN-20240315-001234',
        'alert_type': '高額海外送金',
        'expected_branch': 'escalation',
        'expected_risk': 'HIGH',
        'check_description': 'Code ノードで risk_level: HIGH が抽出され、エスカレーション分岐に進むか',
    },
    {
        'id': 'TC-20',
        'title': 'LOW リスク → 通常処理',
        'transaction_id': 'TXN-20240320-005678',
        'alert_type': '少額頻回取引',
        'expected_branch': 'normal',
        'expected_risk': 'LOW',
        'check_description': '通常処理分岐に進み、モニタリング記録がフォーマット通り出力されるか',
    },
    {
        'id': 'TC-21',
        'title': '金額閾値超過 → エスカレーション',
        'transaction_id': 'TXN-20240401-009999',
        'alert_type': '国内大口送金',
        'expected_branch': 'escalation',
        'expected_risk': 'MEDIUM',
        'check_description': 'IF/ELSE の OR 条件（金額>10000000）が正しく評価されるか',
    },
    {
        'id': 'TC-22',
        'title': '特殊文字を含む取引ID',
        'transaction_id': 'TXN/2024+03&15#001',
        'alert_type': '不審なATM取引',
        'expected_branch': 'normal',
        'expected_risk': 'LOW',
        'check_description': 'URLエンコード処理が正しく動作するか（/ → %2F, + → %2B, & → %26, # → %23）',
    },
]


# ─── ワークフロー ノード実装 ───

def node_url_encode(transaction_id: str) -> dict:
    """Node 30400000000002: URLエンコード"""
    return {'transaction_id_enc': urllib.parse.quote(transaction_id, safe='')}


def node_http_get_transaction(transaction_id_enc: str) -> dict:
    """Node 30400000000003: 取引データ取得 (HTTP GET)"""
    url = f'{BASE_URL}/transactions/{transaction_id_enc}'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        body = resp.read().decode('utf-8')
    return {'status_code': status, 'body': body}


def node_data_shaping(api_response: str) -> dict:
    """Node 30400000000004: データ整形 (Code) — YAMLのコードを忠実に再現"""
    try:
        data = json.loads(api_response) if isinstance(api_response, str) else api_response
        txn_id = data.get('transaction_id', 'N/A')
        raw_amount = data.get('amount', 0)
        try:
            cleaned = str(raw_amount).replace(',', '')
            amount = float(cleaned)
        except (TypeError, ValueError):
            amount = 0
        currency = data.get('currency', 'JPY')
        sender = data.get('sender_account', 'N/A')
        receiver = data.get('receiver_account', 'N/A')
        timestamp = data.get('timestamp', 'N/A')
        location = data.get('location', 'N/A')
        channel = data.get('channel', 'N/A')
        summary = (
            f"取引ID: {txn_id}\n"
            f"金額: {amount:,.0f} {currency}\n"
            f"送金元: {sender}\n"
            f"送金先: {receiver}\n"
            f"日時: {timestamp}\n"
            f"場所: {location}\n"
            f"チャネル: {channel}"
        )
        return {'summary': summary, 'amount': amount}
    except Exception:
        return {'summary': 'データ取得エラー', 'amount': 0}


def node_llm_stub(alert_type: str, summary: str, amount: float) -> dict:
    """
    Node 30400000000005: 不正分析 (LLM) — スタブ実装
    実際のLLM呼び出しの代わりに、取引データの特徴からリスク判定を決定論的に生成する。
    LLMプロンプトの判定基準に従う:
      - 高額（1000万超）＋海外/SWIFT → HIGH
      - 少額＋国内＋通常チャネル → LOW
      - 金額は高いが国内 → MEDIUM
    """
    if amount > 10_000_000 and ('Cayman' in summary or 'SWIFT' in summary):
        risk = 'HIGH'
        indicator = '海外タックスヘイブン宛の高額SWIFT送金。不正資金移転の典型パターンと一致。'
        action = '即座にコンプライアンス部門へエスカレーション。送金の一時保留を推奨。'
    elif amount > 10_000_000:
        risk = 'MEDIUM'
        indicator = '高額取引だが国内送金。取引先との関係性を確認する必要あり。'
        action = '取引先の過去取引履歴を確認し、不自然なパターンがないか精査。'
    elif amount <= 100_000:
        risk = 'LOW'
        indicator = '少額の定型取引。通常パターンの範囲内。'
        action = '定期モニタリング対象として記録。追加アクション不要。'
    else:
        risk = 'LOW'
        indicator = '通常の取引パターン内。特段の異常なし。'
        action = '定期モニタリング対象として記録。'

    text = (
        f"■ 取引概要: アラート種別「{alert_type}」に基づく取引分析\n"
        f"■ リスク評価: {risk}\n"
        f"■ 不正指標:\n"
        f"  - {indicator}\n"
        f"■ 推奨アクション: {action}"
    )
    return {'text': text}


def node_risk_extraction(llm_text: str) -> dict:
    """Node 30400000000012: リスク判定抽出 (Code) — YAMLのコードを忠実に再現"""
    risk_level = "UNKNOWN"
    match = re.search(r'リスク評価[:：]\s*(HIGH|MEDIUM|LOW)', llm_text)
    if match:
        risk_level = match.group(1)
    return {'risk_level': risk_level}


def node_if_else(risk_level: str, amount: float) -> str:
    """
    Node 30400000000006: エスカレーション判定 (IF/ELSE)
    条件: risk_level is "HIGH" OR amount > 10000000
    """
    cond1 = risk_level == "HIGH"
    cond2 = amount > 10_000_000
    return 'true' if (cond1 or cond2) else 'false'


def node_json_build(transaction_id: str, alert_type: str,
                    risk_level: str, analysis: str) -> dict:
    """Node 30400000000007: JSON構築 (Code) — YAMLのコードを忠実に再現"""
    payload = json.dumps({
        "transaction_id": transaction_id,
        "alert_type": alert_type,
        "risk_level": risk_level,
        "analysis": analysis,
        "action": "immediate_review"
    }, ensure_ascii=False)
    return {'payload': payload}


def node_http_post_escalate(payload: str) -> dict:
    """Node 30400000000008: エスカレーション通知 (HTTP POST)"""
    url = f'{BASE_URL}/fraud/escalate'
    data = payload.encode('utf-8')
    req = urllib.request.Request(
        url, data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        body = resp.read().decode('utf-8')
    return {'status_code': status, 'body': body}


def node_template_normal(transaction_id: str, alert_type: str,
                         analysis: str) -> dict:
    """Node 30400000000009: 通常処理 (Template)"""
    output = (
        f"## 不正取引アラート分析結果\n\n"
        f"取引ID: {transaction_id}\n"
        f"アラート種別: {alert_type}\n\n"
        f"### 分析結果\n"
        f"{analysis}\n\n"
        f"### 判定\n"
        f"現時点でエスカレーションは不要です。\n"
        f"定期モニタリングの対象として記録されました。"
    )
    return {'output': output}


# ─── テスト実行 ───

def run_test(tc: dict) -> tuple:
    """
    1つのテストケースについてワークフロー全体をシミュレーション実行する。
    Returns: (passed: bool, details: list[str])
    """
    details = []
    checks_passed = []

    transaction_id = tc['transaction_id']
    alert_type = tc['alert_type']

    # --- Node: URLエンコード ---
    enc_result = node_url_encode(transaction_id)
    encoded_id = enc_result['transaction_id_enc']
    details.append(f'  URLエンコード: {transaction_id} → {encoded_id}')

    if tc['id'] == 'TC-22':
        # 特殊文字確認
        expected_chars = {'%2F': '/', '%2B': '+', '%26': '&', '%23': '#'}
        all_encoded = all(k in encoded_id for k in expected_chars)
        mark = f'{GREEN}OK{RESET}' if all_encoded else f'{RED}NG{RESET}'
        details.append(f'  特殊文字エンコード: {mark}')
        checks_passed.append(all_encoded)

    # --- Node: HTTP GET 取引データ ---
    try:
        http_result = node_http_get_transaction(encoded_id)
        details.append(f'  HTTP GET /transactions: status={http_result["status_code"]}')
        checks_passed.append(http_result['status_code'] == 200)
    except urllib.error.HTTPError as e:
        details.append(f'  HTTP GET /transactions: {RED}ERROR status={e.code}{RESET}')
        checks_passed.append(False)
        return (False, details)

    # --- Node: データ整形 ---
    shaped = node_data_shaping(http_result['body'])
    details.append(f'  データ整形: amount={shaped["amount"]:,.0f} JPY')

    # --- Node: LLM 不正分析 (スタブ) ---
    llm_result = node_llm_stub(alert_type, shaped['summary'], shaped['amount'])
    details.append(f'  LLM分析(スタブ):')
    for line in llm_result['text'].split('\n'):
        details.append(f'    {line}')

    # --- Node: リスク判定抽出 ---
    risk_result = node_risk_extraction(llm_result['text'])
    extracted_risk = risk_result['risk_level']
    risk_match = extracted_risk == tc['expected_risk']
    mark = f'{GREEN}OK{RESET}' if risk_match else f'{YELLOW}WARN{RESET}'
    details.append(f'  リスク抽出: {extracted_risk} (期待: {tc["expected_risk"]}) {mark}')
    checks_passed.append(risk_match)

    # --- Node: IF/ELSE エスカレーション判定 ---
    branch = node_if_else(extracted_risk, shaped['amount'])
    expected_branch_bool = 'true' if tc['expected_branch'] == 'escalation' else 'false'
    branch_match = branch == expected_branch_bool
    branch_label = 'エスカレーション' if branch == 'true' else '通常処理'
    expected_label = 'エスカレーション' if tc['expected_branch'] == 'escalation' else '通常処理'
    mark = f'{GREEN}OK{RESET}' if branch_match else f'{RED}NG{RESET}'
    details.append(f'  IF/ELSE判定: {branch_label} (期待: {expected_label}) {mark}')

    if tc['id'] == 'TC-21':
        details.append(f'    ※ risk_level={extracted_risk}(非HIGH) だが amount={shaped["amount"]:,.0f} > 10,000,000 で OR条件成立')

    checks_passed.append(branch_match)

    # --- 分岐先ノード ---
    if branch == 'true':
        # JSON構築 → HTTP POST エスカレーション
        json_result = node_json_build(transaction_id, alert_type,
                                      extracted_risk, llm_result['text'])
        payload_obj = json.loads(json_result['payload'])
        details.append(f'  JSON構築:')
        details.append(f'    risk_level in payload: "{payload_obj["risk_level"]}"')

        # risk_level がハードコードでないことを確認
        risk_in_payload = payload_obj['risk_level'] == extracted_risk
        mark = f'{GREEN}OK{RESET}' if risk_in_payload else f'{RED}NG (ハードコード "HIGH" のまま?){RESET}'
        details.append(f'    risk_level 動的反映: {mark}')
        checks_passed.append(risk_in_payload)

        try:
            esc_result = node_http_post_escalate(json_result['payload'])
            esc_body = json.loads(esc_result['body'])
            esc_ok = esc_result['status_code'] == 200 and esc_body.get('status') == 'received'
            mark = f'{GREEN}OK{RESET}' if esc_ok else f'{RED}NG{RESET}'
            details.append(f'  エスカレーション通知: status={esc_result["status_code"]}, '
                          f'escalation_id={esc_body.get("escalation_id", "N/A")} {mark}')
            checks_passed.append(esc_ok)
        except Exception as e:
            details.append(f'  エスカレーション通知: {RED}ERROR {e}{RESET}')
            checks_passed.append(False)
    else:
        # 通常処理テンプレート
        tmpl_result = node_template_normal(transaction_id, alert_type, llm_result['text'])
        has_header = '## 不正取引アラート分析結果' in tmpl_result['output']
        has_no_esc = 'エスカレーションは不要' in tmpl_result['output']
        tmpl_ok = has_header and has_no_esc
        mark = f'{GREEN}OK{RESET}' if tmpl_ok else f'{RED}NG{RESET}'
        details.append(f'  通常処理テンプレート: ヘッダー={has_header}, 判定文={has_no_esc} {mark}')
        checks_passed.append(tmpl_ok)

    passed = all(checks_passed)
    return (passed, details)


def main():
    print(f'{BOLD}{"=" * 70}{RESET}')
    print(f'{BOLD}BNK-04 不正取引アラート — TC-19〜22 ワークフローシミュレーション{RESET}')
    print(f'{BOLD}{"=" * 70}{RESET}')
    print(f'対象: モックAPI {BASE_URL}')
    print(f'LLMノード: 決定論的スタブで代替（判定基準はプロンプト仕様に準拠）')
    print()

    results = []

    for tc in TEST_CASES:
        print(f'{BOLD}--- {tc["id"]}: {tc["title"]} ---{RESET}')
        print(f'  入力: transaction_id={tc["transaction_id"]}, alert_type={tc["alert_type"]}')
        print(f'  確認観点: {tc["check_description"]}')
        print()

        try:
            passed, details = run_test(tc)
        except Exception as e:
            passed = False
            details = [f'  {RED}FATAL ERROR: {e}{RESET}']

        for line in details:
            print(line)

        verdict = f'{GREEN}{BOLD}PASS{RESET}' if passed else f'{RED}{BOLD}FAIL{RESET}'
        print()
        print(f'  結果: {verdict}')
        print()
        results.append((tc['id'], tc['title'], passed))

    # ─── サマリー ───
    print(f'{BOLD}{"=" * 70}{RESET}')
    print(f'{BOLD}結果サマリー{RESET}')
    print(f'{BOLD}{"=" * 70}{RESET}')

    pass_count = sum(1 for _, _, p in results if p)
    fail_count = len(results) - pass_count

    for tc_id, title, passed in results:
        mark = f'{GREEN}PASS{RESET}' if passed else f'{RED}FAIL{RESET}'
        print(f'  {tc_id}: {title} ... {mark}')

    print()
    print(f'  {BOLD}{pass_count}/{len(results)} passed{RESET}', end='')
    if fail_count:
        print(f', {RED}{fail_count} failed{RESET}')
    else:
        print(f' {GREEN}— All clear!{RESET}')
    print()

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == '__main__':
    main()
