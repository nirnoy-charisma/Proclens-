from flask import Flask, render_template, jsonify, request
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from engine.collector  import get_snapshot, get_sim_snapshot
from engine.scheduler  import compare_from_snapshot
from engine.explainer  import ask_gemini, ask_friendly
from config import MAX_HISTORY

app = Flask(__name__)
history  = []
sim_tick = [0]

def _get_snap(mode):
    try:
        return get_snapshot() if mode == 'live' else get_sim_snapshot(sim_tick[0])
    except:
        return get_sim_snapshot(sim_tick[0])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/snapshot')
def snapshot():
    mode = request.args.get('mode', 'live')
    data = _get_snap(mode)
    if mode == 'sim': sim_tick[0] += 1
    history.append({'ts_ms': data['ts_ms'], 'cpu': data['cpu']['total'], 'mem': data['mem']['pct']})
    if len(history) > MAX_HISTORY: history.pop(0)
    data['history'] = list(history[-30:])
    if 'states' not in data: data['states'] = {}
    return jsonify(data)

@app.route('/api/compare')
def compare():
    mode = request.args.get('mode', 'live')
    snap = _get_snap(mode)
    return jsonify(compare_from_snapshot(snap['procs']))

@app.route('/api/explain', methods=['POST'])
def explain():
    body = request.json or {}
    snap = _get_snap(body.get('mode', 'live'))
    cmp  = compare_from_snapshot(snap['procs'])
    return jsonify({'explanation': ask_gemini(snap, cmp)})

@app.route('/api/explain_friendly', methods=['POST'])
def explain_friendly():
    body = request.json or {}
    snap = _get_snap(body.get('mode', 'live'))
    return jsonify({'explanation': ask_friendly(snap)})

@app.route('/api/history')
def get_history():
    return jsonify(history)

if __name__ == '__main__':
    print("\n  🔬 ProcLens is running → http://localhost:5000\n")
    app.run(debug=True, port=5000)
