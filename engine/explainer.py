import requests, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_URL

TECH_SYSTEM = """You are an OS internals expert in a system monitoring tool called ProcLens.
Structure your response exactly like this:

**🔍 What's Happening**
2-3 sentences describing the current system state.

**⚙️ OS Theory**
Explain using real OS concepts (scheduling, paging, thrashing, context switching, I/O wait).

**⚠️ Bottlenecks**
List 1-3 specific bottlenecks. Name actual processes.

**💡 Recommendations**
2-3 actionable suggestions grounded in OS theory.

**📊 Verdict**
One sentence summary. End with: Score: X/10

Under 300 words. Be direct and technical."""

FRIENDLY_SYSTEM = """You are a friendly PC helper talking to someone who is NOT a tech person.
Structure your response exactly like this:

**How is your PC doing right now?**
1-2 sentences in plain English. Use a simple analogy if helpful.

**The biggest thing slowing you down**
Name the specific app and explain in one sentence why it matters. No jargon.

**3 things to do right now**
1. First action
2. Second action
3. Third action

**One habit to keep your PC fast**
One friendly tip they can remember.

Under 200 words. Sound like a helpful friend, not a textbook."""

def _call_groq(system, prompt):
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens":  600,
    }
    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type":  "application/json",
    }
    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        data = r.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            return "**Error:** " + data["error"].get("message", "Unknown error")
        return "**Error:** Unexpected response."
    except requests.Timeout:
        return "**Error:** Request timed out."
    except Exception as e:
        return "**Error:** " + str(e)

def build_prompt(snapshot, comparison=None):
    cpu    = snapshot['cpu']
    mem    = snapshot['mem']
    top    = snapshot['procs'][:6]
    states = snapshot.get('states', {})
    mode   = snapshot.get('mode', 'live')
    proc_lines = "\n".join(
        "  - " + p['name'] + " (PID " + str(p['pid']) + "): CPU " + str(p['cpu']) + "%, MEM " + str(p['mem_pct']) + "%, status=" + p['status']
        for p in top
    )
    cmp_lines = ""
    if comparison:
        for algo, data in comparison['algorithms'].items():
            a = data['averages']
            cmp_lines += "  " + algo + ": avg_wait=" + str(a['avg_wt']) + "  avg_tat=" + str(a['avg_tat']) + "\n"
        cmp_lines = "\nScheduling Comparison:\n" + cmp_lines + "Best: " + comparison['best_wt']
    return ("System Snapshot (" + ('LIVE' if mode=='live' else 'SIMULATION') + "):\n"
            "CPU: " + str(cpu['total']) + "% across " + str(cpu['count']) + " cores\n"
            "Memory: " + str(mem['used']) + "MB / " + str(mem['total']) + "MB (" + str(mem['pct']) + "%)\n"
            "Swap: " + str(mem['swap_used']) + "MB / " + str(mem['swap_total']) + "MB (" + str(mem['swap_pct']) + "%)\n"
            "Process States: " + json.dumps(states) + "\n"
            "Total Processes: " + str(snapshot['proc_count']) + "\n\n"
            "Top Processes:\n" + proc_lines + "\n" + cmp_lines + "\nAnalyze this.")

def build_friendly_prompt(snapshot):
    cpu  = snapshot['cpu']['total']
    mem  = snapshot['mem']['pct']
    swap = snapshot['mem']['swap_pct']
    top  = snapshot['procs'][:5]
    proc_lines = "\n".join("  - " + p['name'] + ": CPU " + str(p['cpu']) + "%, Memory " + str(p['mem_pct']) + "%" for p in top)
    return ("Computer status:\n"
            "- Processor usage: " + str(cpu) + "%\n"
            "- Memory (RAM) usage: " + str(mem) + "%\n"
            "- Emergency memory (swap): " + str(swap) + "%\n"
            "- Biggest apps running:\n" + proc_lines + "\n\nGive friendly advice.")

def ask_gemini(snapshot, comparison=None):
    return _call_groq(TECH_SYSTEM, build_prompt(snapshot, comparison))

def ask_friendly(snapshot):
    return _call_groq(FRIENDLY_SYSTEM, build_friendly_prompt(snapshot))
