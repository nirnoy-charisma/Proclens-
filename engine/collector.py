import psutil, time, random, math
from datetime import datetime

def get_snapshot():
    cpu_total    = psutil.cpu_percent(interval=0.1)
    cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    mem  = psutil.virtual_memory()
    swap = psutil.swap_memory()
    try:    dio = psutil.disk_io_counters(); dr, dw = dio.read_bytes, dio.write_bytes
    except: dr = dw = 0
    try:    nio = psutil.net_io_counters();  ns, nr = nio.bytes_sent, nio.bytes_recv
    except: ns = nr = 0

    procs = []
    for p in psutil.process_iter(['pid','name','status','cpu_percent','memory_percent','num_threads','ppid','nice','create_time']):
        try:
            i = p.info
            try:    rss = p.memory_info().rss // 1024
            except: rss = 0
            try:    io = p.io_counters(); ior, iow = io.read_bytes, io.write_bytes
            except: ior = iow = 0
            procs.append({'pid':i['pid'],'name':i['name'] or '?','status':i['status'] or '?',
                          'cpu':round(i['cpu_percent'] or 0,1),'mem_pct':round(i['memory_percent'] or 0,2),
                          'mem_kb':rss,'threads':i['num_threads'] or 1,'ppid':i['ppid'] or 0,
                          'nice':i['nice'] or 0,'io_r':ior,'io_w':iow})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x['cpu'], reverse=True)
    sc = {}
    for p in procs: sc[p['status']] = sc.get(p['status'],0)+1

    return {
        'ts': datetime.now().isoformat(), 'ts_ms': int(time.time()*1000),
        'cpu': {'total': cpu_total, 'cores': cpu_per_core, 'count': len(cpu_per_core)},
        'mem': {'total': round(mem.total/1048576), 'used': round(mem.used/1048576),
                'avail': round(mem.available/1048576), 'pct': mem.percent,
                'swap_total': round(swap.total/1048576), 'swap_used': round(swap.used/1048576), 'swap_pct': swap.percent},
        'disk': {'r': dr, 'w': dw}, 'net': {'s': ns, 'r': nr},
        'procs': procs[:40], 'proc_count': len(procs), 'states': sc, 'mode': 'live'
    }


def get_sim_snapshot(tick=0):
    random.seed(tick)
    base = 30 + 25 * abs(math.sin(tick * 0.25)) + random.random()*8
    mu = 4800 + int(400*math.sin(tick*0.1)) + random.randint(0,300)
    procs = [
        {'pid':1,   'name':'systemd',  'status':'sleeping','cpu':0.0,                         'mem_pct':0.1,'mem_kb':8192,  'threads':1, 'ppid':0, 'nice':0,  'io_r':0,    'io_w':0},
        {'pid':423, 'name':'python3',  'status':'running', 'cpu':round(14+random.random()*12,1),'mem_pct':2.1,'mem_kb':52000,'threads':3, 'ppid':1, 'nice':0,  'io_r':1024, 'io_w':512},
        {'pid':512, 'name':'chrome',   'status':'running', 'cpu':round(9+random.random()*14,1), 'mem_pct':8.4,'mem_kb':210000,'threads':14,'ppid':1, 'nice':0,  'io_r':2048, 'io_w':256},
        {'pid':634, 'name':'node',     'status':'sleeping','cpu':round(random.random()*6,1),    'mem_pct':3.2,'mem_kb':83000,'threads':6, 'ppid':1, 'nice':0,  'io_r':512,  'io_w':128},
        {'pid':701, 'name':'postgres', 'status':'sleeping','cpu':round(random.random()*4,1),    'mem_pct':1.8,'mem_kb':47000,'threads':4, 'ppid':1, 'nice':0,  'io_r':4096, 'io_w':2048},
        {'pid':812, 'name':'code',     'status':'running', 'cpu':round(6+random.random()*9,1),  'mem_pct':5.6,'mem_kb':145000,'threads':8,'ppid':1, 'nice':0,  'io_r':1024, 'io_w':768},
        {'pid':923, 'name':'ffmpeg',   'status':'running', 'cpu':round(18+random.random()*16,1),'mem_pct':1.2,'mem_kb':31000,'threads':2, 'ppid':1, 'nice':5,  'io_r':8192, 'io_w':4096},
        {'pid':1024,'name':'slack',    'status':'sleeping','cpu':round(random.random()*3,1),    'mem_pct':4.1,'mem_kb':104000,'threads':10,'ppid':1,'nice':0,  'io_r':256,  'io_w':128},
        {'pid':1100,'name':'kworker',  'status':'idle',    'cpu':0.0,                          'mem_pct':0.0,'mem_kb':0,    'threads':1, 'ppid':0, 'nice':-20,'io_r':0,    'io_w':0},
        {'pid':1201,'name':'sshd',     'status':'sleeping','cpu':0.0,                          'mem_pct':0.1,'mem_kb':4096, 'threads':1, 'ppid':1, 'nice':0,  'io_r':0,    'io_w':0},
    ]
    procs.sort(key=lambda x: x['cpu'], reverse=True)
    return {
        'ts': datetime.now().isoformat(), 'ts_ms': int(time.time()*1000),
        'cpu': {'total': round(base,1), 'cores': [round(base*(0.6+random.random()*0.8),1) for _ in range(8)], 'count': 8},
        'mem': {'total':16384,'used':mu,'avail':16384-mu,'pct':round(mu/163.84,1),
                'swap_total':8192,'swap_used':random.randint(0,600),'swap_pct':round(random.random()*7,1)},
        'disk': {'r': tick*4096, 'w': tick*2048}, 'net': {'s': tick*1024, 'r': tick*2048},
        'procs': procs, 'proc_count': len(procs),
        'states': {'running':4,'sleeping':5,'idle':1}, 'mode': 'simulation'
    }
