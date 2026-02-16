"""
Banking テスト環境 疎通確認スクリプト

使用方法:
  1. モックサーバーを起動: cd mock-server && python app.py
  2. 別ターミナルで実行: python scripts/verify-setup.py

全エンドポイントにリクエストを送信し、レスポンスを検証する。
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = 'http://localhost:5001'

passed = 0
failed = 0
errors = []


def test(name, method, path, expected_status=200, expected_fields=None,
         post_data=None, check_fn=None):
    """単一テスト実行"""
    global passed, failed, errors

    url = BASE_URL + path
    print(f'  [{method}] {path} ... ', end='', flush=True)

    try:
        if method == 'POST' and post_data is not None:
            data = json.dumps(post_data).encode('utf-8')
            req = urllib.request.Request(
                url, data=data,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
        else:
            req = urllib.request.Request(url, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                body = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            status = e.code
            body = json.loads(e.read().decode('utf-8'))

        # ステータスコード確認
        if status != expected_status:
            print(f'FAIL (status {status}, expected {expected_status})')
            errors.append(f'{name}: status {status} != {expected_status}')
            failed += 1
            return

        # 必須フィールド確認
        if expected_fields:
            missing = [f for f in expected_fields if f not in body]
            if missing:
                print(f'FAIL (missing fields: {missing})')
                errors.append(f'{name}: missing fields {missing}')
                failed += 1
                return

        # カスタムチェック
        if check_fn:
            ok, msg = check_fn(body)
            if not ok:
                print(f'FAIL ({msg})')
                errors.append(f'{name}: {msg}')
                failed += 1
                return

        print('OK')
        passed += 1

    except urllib.error.URLError as e:
        print(f'ERROR ({e.reason})')
        errors.append(f'{name}: connection error - {e.reason}')
        failed += 1
    except Exception as e:
        print(f'ERROR ({e})')
        errors.append(f'{name}: {e}')
        failed += 1


def main():
    global passed, failed, errors

    print('=' * 60)
    print('Banking Mock API - 疎通確認')
    print('=' * 60)
    print()

    # --- Health ---
    print('[Health Check]')
    test(
        'Health',
        'GET', '/health',
        expected_fields=['status', 'endpoints', 'fixtures'],
    )
    print()

    # --- Transactions (BNK-04) ---
    print('[Transactions - BNK-04]')

    # TC-19: 高額海外取引
    test(
        'TC-19 高額海外取引',
        'GET', '/transactions/TXN-20240315-001234',
        expected_fields=['transaction_id', 'amount', 'currency',
                         'sender_account', 'receiver_account',
                         'timestamp', 'location', 'channel'],
        check_fn=lambda b: (b['amount'] == 52000000, f'amount={b["amount"]}'),
    )

    # TC-20: 少額国内取引
    test(
        'TC-20 少額国内取引',
        'GET', '/transactions/TXN-20240320-005678',
        expected_fields=['transaction_id', 'amount'],
        check_fn=lambda b: (b['amount'] == 35000, f'amount={b["amount"]}'),
    )

    # TC-21: 金額閾値テスト
    test(
        'TC-21 金額閾値テスト',
        'GET', '/transactions/TXN-20240401-009999',
        expected_fields=['transaction_id', 'amount'],
        check_fn=lambda b: (b['amount'] == 15000000, f'amount={b["amount"]}'),
    )

    # TC-22: URL特殊文字
    encoded_id = urllib.parse.quote('TXN/2024+03&15#001', safe='')
    test(
        'TC-22 URL特殊文字',
        'GET', f'/transactions/{encoded_id}',
        expected_fields=['transaction_id', 'amount'],
        check_fn=lambda b: (b['transaction_id'] == 'TXN/2024+03&15#001',
                            f'id={b["transaction_id"]}'),
    )

    # 存在しない取引
    test(
        'Transaction 404',
        'GET', '/transactions/NONEXISTENT',
        expected_status=404,
        expected_fields=['error'],
    )
    print()

    # --- Fraud Escalation (BNK-04) ---
    print('[Fraud Escalation - BNK-04]')
    test(
        'Escalation POST',
        'POST', '/fraud/escalate',
        expected_fields=['status', 'escalation_id', 'timestamp'],
        post_data={'transaction_id': 'TXN-20240315-001234', 'risk_level': 'HIGH'},
        check_fn=lambda b: (b['status'] == 'received', f'status={b["status"]}'),
    )
    print()

    # --- Branch Performance (BNK-05) ---
    print('[Branch Performance - BNK-05]')

    # TC-23: 東京中央支店
    test(
        'TC-23 東京中央支店',
        'GET', '/branch-performance?branch=BR-001&period=2024Q3',
        expected_fields=['branch_code', 'branch_name', 'deposits_billion',
                         'loans_billion', 'profit_million', 'new_accounts'],
        check_fn=lambda b: (b['branch_name'] == '東京中央支店',
                            f'name={b["branch_name"]}'),
    )

    # パラメータなし
    test(
        'Branch missing param',
        'GET', '/branch-performance',
        expected_status=400,
        expected_fields=['error'],
    )

    # 存在しない支店
    test(
        'Branch 404',
        'GET', '/branch-performance?branch=BR-999',
        expected_status=404,
        expected_fields=['error'],
    )
    print()

    # --- FX Rate (BNK-08) ---
    print('[FX Rate - BNK-08]')

    # TC-36: USD/JPY
    test(
        'TC-36 USD/JPY',
        'GET', '/fx-rate?pair=USD/JPY',
        expected_fields=['pair', 'bid', 'ask', 'change_24h_percent',
                         'high_24h', 'low_24h', 'timestamp'],
        check_fn=lambda b: (b['pair'] == 'USD/JPY', f'pair={b["pair"]}'),
    )

    # TC-37: EUR/JPY
    test(
        'TC-37 EUR/JPY',
        'GET', '/fx-rate?pair=EUR/JPY',
        expected_fields=['pair', 'bid', 'ask'],
    )

    # TC-38: GBP/JPY
    test(
        'TC-38 GBP/JPY',
        'GET', '/fx-rate?pair=GBP/JPY',
        expected_fields=['pair', 'bid', 'ask'],
    )

    # TC-39: AUD/JPY
    test(
        'TC-39 AUD/JPY',
        'GET', '/fx-rate?pair=AUD/JPY',
        expected_fields=['pair', 'bid', 'ask'],
    )

    # TC-40: THB/JPY（未対応通貨 → 200 + error）
    test(
        'TC-40 THB/JPY (unsupported)',
        'GET', '/fx-rate?pair=THB/JPY',
        expected_status=200,
        expected_fields=['error'],
        check_fn=lambda b: ('Unsupported' in b.get('error', ''),
                            f'error={b.get("error")}'),
    )

    # パラメータなし
    test(
        'FX missing param',
        'GET', '/fx-rate',
        expected_status=400,
        expected_fields=['error'],
    )
    print()

    # --- 結果サマリー ---
    print('=' * 60)
    total = passed + failed
    print(f'結果: {passed}/{total} passed, {failed}/{total} failed')

    if errors:
        print()
        print('失敗詳細:')
        for err in errors:
            print(f'  - {err}')

    print('=' * 60)

    # --- ナレッジベースファイル確認 ---
    print()
    print('[Knowledge Base Files]')
    import os
    kb_dir = os.path.join(os.path.dirname(__file__), '..', 'knowledge-bases')
    kb_files = {
        'compliance-kb.md': 'BNK-01 コンプライアンス規程',
        'account-kb.md': 'BNK-03 口座サービスご案内',
    }
    for filename, desc in kb_files.items():
        path = os.path.join(kb_dir, filename)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f'  {filename} ({desc}): OK ({size:,} bytes)')
        else:
            print(f'  {filename} ({desc}): MISSING')
            failed += 1

    print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
