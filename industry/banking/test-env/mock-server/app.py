"""
Banking Workflow テスト用モックAPIサーバー

対象ワークフロー:
  - BNK-04: 取引モニタリング（不正検知）
  - BNK-05: 支店実績レポート
  - BNK-08: 為替レート照会

起動: python app.py
ポート: 5001（macOS AirPlay の 5000 回避）
"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# --- フィクスチャ読み込み ---

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

def load_json(filename):
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 起動時にメモリへ読み込み
transactions_list = load_json('transactions.json')      # list
branches_list = load_json('branches.json')               # list
fx_rates = load_json('fx-rates.json')                    # dict keyed by pair

# transactions を id → record の辞書に変換
transactions = {t['transaction_id']: t for t in transactions_list}
# branches を branch_code → record の辞書に変換
branches = {b['branch_code']: b for b in branches_list}

# エスカレーションログファイル
ESCALATION_LOG = os.path.join(os.path.dirname(__file__), 'escalation.log')

JST = timezone(timedelta(hours=9))


# --- CORS ---

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response


# --- エンドポイント ---

@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return jsonify({
        'status': 'ok',
        'service': 'banking-mock-api',
        'endpoints': [
            '/transactions/<id>',
            '/fraud/escalate',
            '/branch-performance',
            '/fx-rate',
        ],
        'fixtures': {
            'transactions': len(transactions),
            'branches': len(branches),
            'fx_rates': len(fx_rates),
        },
    })


@app.route('/transactions/<path:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """
    BNK-04 用: 取引データ取得
    <path:> コンバータで '/' を含む ID にも対応（TC-22）
    """
    record = transactions.get(transaction_id)
    if record is None:
        return jsonify({
            'error': f'Transaction not found: {transaction_id}',
            'available_ids': list(transactions.keys()),
        }), 404
    return jsonify(record)


@app.route('/fraud/escalate', methods=['POST', 'OPTIONS'])
def fraud_escalate():
    """
    BNK-04 用: 不正取引エスカレーション受付
    受信ログを記録し、常に 200 を返却
    """
    if request.method == 'OPTIONS':
        return '', 204

    body = request.get_json(silent=True) or {}
    escalation_id = f'ESC-{uuid.uuid4().hex[:8].upper()}'
    now = datetime.now(JST).isoformat()

    # ログファイルに追記
    log_entry = {
        'escalation_id': escalation_id,
        'timestamp': now,
        'payload': body,
    }
    with open(ESCALATION_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    return jsonify({
        'status': 'received',
        'escalation_id': escalation_id,
        'timestamp': now,
    })


@app.route('/branch-performance', methods=['GET'])
def branch_performance():
    """
    BNK-05 用: 支店実績データ取得
    クエリパラメータ: branch (支店コード), period (任意)
    """
    branch_code = request.args.get('branch')
    period = request.args.get('period', '2024Q3')

    if not branch_code:
        return jsonify({
            'error': 'branch parameter is required',
            'example': '/branch-performance?branch=BR-001&period=2024Q3',
            'available_branches': list(branches.keys()),
        }), 400

    record = branches.get(branch_code)
    if record is None:
        return jsonify({
            'error': f'Branch not found: {branch_code}',
            'available_branches': list(branches.keys()),
        }), 404

    # period をレスポンスに含める
    result = dict(record)
    result['period'] = period
    return jsonify(result)


@app.route('/fx-rate', methods=['GET'])
def fx_rate():
    """
    BNK-08 用: 為替レート取得
    クエリパラメータ: pair (通貨ペア, e.g. USD/JPY)

    THB/JPY 等の未対応ペアは HTTP 200 で error フィールドを返す
    （404 だと Dify の HTTP Request ノードがエラー停止するため）
    """
    pair = request.args.get('pair')

    if not pair:
        return jsonify({
            'error': 'pair parameter is required',
            'example': '/fx-rate?pair=USD/JPY',
            'available_pairs': list(fx_rates.keys()),
        }), 400

    record = fx_rates.get(pair)
    if record is None:
        # 未対応通貨ペア: 200 で error を返す（TC-40 THB/JPY 等）
        return jsonify({
            'error': f'Unsupported currency pair: {pair}',
            'supported_pairs': list(fx_rates.keys()),
        })

    return jsonify(record)


# --- メイン ---

if __name__ == '__main__':
    print('=== Banking Mock API Server ===')
    print(f'Fixtures loaded:')
    print(f'  Transactions: {len(transactions)} records')
    print(f'  Branches:     {len(branches)} records')
    print(f'  FX Rates:     {len(fx_rates)} pairs')
    print()
    print('Endpoints:')
    print('  GET  /health')
    print('  GET  /transactions/<id>')
    print('  POST /fraud/escalate')
    print('  GET  /branch-performance?branch=<code>&period=<period>')
    print('  GET  /fx-rate?pair=<pair>')
    print()
    app.run(host='0.0.0.0', port=5001, debug=True)
