import json
import traceback
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from odoo_api import OdooAPI
from generators import DemoGenerator, DEFAULT_COUNTS

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    url = data.get('url', '').strip()
    db = data.get('db', '').strip()
    login = data.get('login', '').strip()
    api_key = data.get('api_key', '').strip()

    print(f"\n{'='*60}")
    print(f"Generate request received")
    print(f"  URL: {url}")
    print(f"  DB: {db}")
    print(f"  Login: {login}")
    print(f"  API Key: {'*' * len(api_key) if api_key else '(empty)'}")
    print(f"{'='*60}")

    if not all([url, db, login, api_key]):
        return jsonify({'success': False, 'error': 'All connection fields are required.'}), 400

    # Always generate all data types with default counts
    selections = dict(DEFAULT_COUNTS)

    def event_stream():
        # Tell frontend how many steps: auth + modules + configure + each data type + mto_showcase + publish_website
        total_steps = 2 + 1 + len(selections) + 2
        yield json.dumps({'type': '_total', 'count': total_steps}) + '\n'

        # Authenticate
        yield json.dumps({'type': 'auth', 'status': 'working', 'detail': 'Connecting...'}) + '\n'
        try:
            api = OdooAPI(url, db, login, api_key)
            uid = api.authenticate()
            print(f"Authenticated as UID: {uid}")
            yield json.dumps({'type': 'auth', 'status': 'done', 'detail': 'Connected'}) + '\n'
        except Exception as e:
            print(f"AUTH FAILED: {e}")
            traceback.print_exc()
            yield json.dumps({'type': 'auth', 'status': 'error', 'detail': str(e)[:200]}) + '\n'
            return

        # Generate
        generator = DemoGenerator(api)
        for event in generator.generate(selections):
            yield json.dumps(event) + '\n'

    return Response(stream_with_context(event_stream()), content_type='application/x-ndjson')


if __name__ == '__main__':
    app.run(debug=True, port=5088)
