import copy
from collections import deque

def _make_procs(snapshot_procs):
    """Convert top N CPU processes into scheduling inputs."""
    result = []
    for i, p in enumerate(snapshot_procs[:6]):
        result.append({
            'pid': p['name'][:8],
            'arrival': i,
            'burst': max(1, int(p['cpu'] * 2) or (i+1)*2),
            'priority': i+1,
        })
    return result if result else [{'pid':'P1','arrival':0,'burst':5,'priority':1}]

def _fcfs(procs):
    t, tl = 0, []
    for p in sorted(procs, key=lambda x: x['arrival']):
        s = max(t, p['arrival']); e = s + p['burst']
        tl.append({'pid':p['pid'],'start':s,'end':e}); t = e
    return tl

def _rr(procs, q=3):
    ps = copy.deepcopy(sorted(procs, key=lambda x: x['arrival']))
    for p in ps: p['rem'] = p['burst']
    queue, tl, t, i = deque(), [], 0, 0
    while i < len(ps) and ps[i]['arrival'] <= t: queue.append(ps[i]); i+=1
    while queue or i < len(ps):
        if not queue: t = ps[i]['arrival']; queue.append(ps[i]); i+=1; continue
        p = queue.popleft(); run = min(q, p['rem'])
        tl.append({'pid':p['pid'],'start':t,'end':t+run}); t += run; p['rem'] -= run
        while i < len(ps) and ps[i]['arrival'] <= t: queue.append(ps[i]); i+=1
        if p['rem'] > 0: queue.append(p)
    return tl

def _sjf(procs):
    rem = copy.deepcopy(procs); tl = []; t = 0
    while rem:
        avail = [p for p in rem if p['arrival'] <= t]
        if not avail: t = min(p['arrival'] for p in rem); continue
        p = min(avail, key=lambda x: x['burst']); rem.remove(p)
        tl.append({'pid':p['pid'],'start':t,'end':t+p['burst']}); t += p['burst']
    return tl

def _stats(procs, tl):
    out = {}
    for p in procs:
        segs = [s for s in tl if s['pid']==p['pid']]
        if not segs: continue
        fin = max(s['end'] for s in segs); fst = min(s['start'] for s in segs)
        out[p['pid']] = {'wt': fin-p['arrival']-p['burst'], 'tat': fin-p['arrival'], 'rt': fst-p['arrival']}
    n = len(out)
    return out, {
        'avg_wt':  round(sum(v['wt']  for v in out.values())/n, 2) if n else 0,
        'avg_tat': round(sum(v['tat'] for v in out.values())/n, 2) if n else 0,
        'avg_rt':  round(sum(v['rt']  for v in out.values())/n, 2) if n else 0,
    }

def compare_from_snapshot(snapshot_procs):
    procs = _make_procs(snapshot_procs)
    results = {}
    for name, fn in [('FCFS', _fcfs), ('SJF', _sjf), ('RR(q=3)', lambda p: _rr(p,3))]:
        tl = fn(procs)
        _, avgs = _stats(procs, tl)
        results[name] = {'timeline': tl, 'averages': avgs}
    best_wt = min(results, key=lambda k: results[k]['averages']['avg_wt'])
    return {'algorithms': results, 'processes': procs, 'best_wt': best_wt}
