import os, json, gzip, hashlib, time, glob
from flask import Flask, jsonify, request, send_from_directory, Response
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv; load_dotenv(os.path.join(ROOT, ".env"))
except ImportError: pass
from config import CFG
app = Flask(__name__, static_folder=None)
CACHE = os.path.join(ROOT, CFG["paths"]["cache"]); MODELS = os.path.join(ROOT, CFG["paths"]["models"])
STATE = dict(verified=None, error=None, building=False)
def cpath(p): return os.path.join(CACHE, p, "connectome.json.gz")
def soma(s):
    if isinstance(s, dict): s = s.get("coordinates")
    try: return [float(s[0]), float(s[1]), float(s[2])]
    except Exception: return None

def cxpath(): return os.path.join(CACHE, "context.json.gz")
def client():
    from neuprint import Client
    tok = os.environ.get("NEUPRINT_TOKEN")
    if not tok: raise RuntimeError("NEUPRINT_TOKEN missing in .env")
    c = Client(CFG["neuprint"]["server"], dataset=CFG["neuprint"]["dataset"], token=tok); STATE["verified"] = time.time(); return c
def build_context():
    cc = CFG["context"]; c = client()
    df = c.fetch_custom(f"MATCH (n:Neuron) WHERE n.somaLocation IS NOT NULL AND n.bodyId % {cc['mod']} = 0 "
        f"AND NOT (coalesce(n.superclass,'') =~ '{cc['exclude']}') "
        f"RETURN n.bodyId AS bodyId, coalesce(n.superclass,'unknown') AS sc, n.somaLocation AS soma LIMIT {cc['max']}")
    classes, out = [], dict(id=[], c=[], x=[], y=[], z=[])
    for r in df.itertuples():
        xyz = soma(r.soma)
        if xyz is None: continue
        if r.sc not in classes: classes.append(r.sc)
        out["id"].append(int(r.bodyId)); out["c"].append(classes.index(r.sc))
        out["x"].append(round(xyz[0])); out["y"].append(round(xyz[1])); out["z"].append(round(xyz[2]))
    if not out["id"]: raise RuntimeError("Outline query returned no neurons")
    out["classes"] = classes; out["note"] = "Real neurons shown for anatomy only; not part of the simulation."
    os.makedirs(CACHE, exist_ok=True)
    with gzip.open(cxpath(), "wt") as f: json.dump(out, f)
    return len(out["id"])

def build(preset):
    from neuprint import Client   # token is read ONLY here, server-side
    tok = os.environ.get("NEUPRINT_TOKEN")
    if not tok: raise RuntimeError("NEUPRINT_TOKEN missing in .env")
    nc = CFG["neuprint"]; cc = CFG["connectome"]; target = cc["presets"][preset]
    c = Client(nc["server"], dataset=nc["dataset"], token=tok)
    STATE["verified"] = time.time()
    ids, rows, dropped = set(), [], {}
    for name, field, rx, share in cc["groups"]:
        lim = max(1, int(target * share))
        df = c.fetch_custom(f"MATCH (n:Neuron) WHERE n.{field} =~ '{rx}' AND n.somaLocation IS NOT NULL "
            f"RETURN n.bodyId AS bodyId, n.type AS type, n.instance AS instance, n.somaLocation AS soma "
            f"ORDER BY coalesce(n.pre,0)+coalesce(n.post,0) DESC LIMIT {lim*2}")
        k = 0
        for r in df.itertuples():
            xyz = soma(r.soma)
            if xyz is None: dropped[name] = dropped.get(name, 0) + 1; continue
            if r.bodyId in ids or k >= lim: continue
            ids.add(r.bodyId); k += 1
            rows.append((int(r.bodyId), r.type or "", r.instance or "", name, *xyz))
    if not rows: raise RuntimeError("No neurons returned; check group rules in config.py")
    idl = [r[0] for r in rows]
    e = c.fetch_custom(f"MATCH (a:Neuron)-[c:ConnectsTo]->(b:Neuron) WHERE a.bodyId IN {idl} AND b.bodyId IN {idl} "
                       f"RETURN a.bodyId AS pre, b.bodyId AS post, c.weight AS w")
    e = e.groupby(["pre", "post"], as_index=False)["w"].sum()
    deg = {}
    for r in e.itertuples(): deg[r.pre] = deg.get(r.pre, 0) + r.w; deg[r.post] = deg.get(r.post, 0) + r.w
    rows = [r for r in rows if r[0] in deg]; idx = {r[0]: i for i, r in enumerate(rows)}   # isolated neurons dropped
    e = e[e.pre.isin(idx) & e.post.isin(idx)]
    insum = e.groupby("post")["w"].sum().to_dict()
    gn = [g[0] for g in cc["groups"]]
    pools = [sorted([r[0] for r in rows if r[3] == g], key=lambda b: -deg[b]) for g in cc["readout_groups"]]
    readout = []
    while len(readout) < cc["readout_size"] and any(pools):
        for p in pools:
            if p and len(readout) < cc["readout_size"]: readout.append(p.pop(0))
    out = dict(
        meta=dict(dataset=nc["dataset"], server=nc["server"], preset=preset, built_at=time.time(), groups=gn,
            counts={g: sum(1 for r in rows if r[3] == g) for g in gn}, n_neurons=len(rows), n_edges=int(len(e)),
            dropped_no_soma=dropped, readout=readout,
            action_mapping=dict(type="computational", note="No biologically defensible Jump/Duck split is claimed; the MLP learns the mapping from the readout neurons.")),
        neurons=dict(id=[r[0] for r in rows], type=[r[1] for r in rows], inst=[r[2] for r in rows],
            grp=[gn.index(r[3]) for r in rows], x=[r[4] for r in rows], y=[r[5] for r in rows], z=[r[6] for r in rows]),
        edges=dict(pre=[idx[a] for a in e.pre], post=[idx[b] for b in e.post], w=[float(w) for w in e.w],
            wn=[float(r.w / insum[r.post]) for r in e.itertuples()]))
    out["meta"]["hash"] = hashlib.sha256(json.dumps([out["neurons"]["id"], out["edges"]["pre"], out["edges"]["post"], out["edges"]["w"]]).encode()).hexdigest()[:16]
    os.makedirs(os.path.dirname(cpath(preset)), exist_ok=True)
    with gzip.open(cpath(preset), "wt") as f: json.dump(out, f)
    return out["meta"]

@app.get("/")
def index(): return send_from_directory(os.path.join(ROOT, "frontend"), "index.html")
@app.get("/api/health")
def health(): return jsonify(ok=True)
@app.get("/api/config")
def config(): return jsonify(CFG)   # no secrets live in CFG
@app.get("/api/connectome/status")
def status():
    pre = {p: os.path.exists(cpath(p)) for p in CFG["connectome"]["presets"]}
    if STATE["building"]: s = "BUILDING"
    elif STATE["error"]: s = "ERROR"
    elif STATE["verified"]: s = "CONNECTED"
    elif any(pre.values()): s = "CACHED"
    else: s = "MISSING"
    return jsonify(status=s, error=STATE["error"], cached=pre)
@app.get("/api/connectome")
def connectome():
    p = request.args.get("preset", CFG["connectome"]["default"])
    if p not in CFG["connectome"]["presets"] or not os.path.exists(cpath(p)): return ("not cached", 404)
    with gzip.open(cpath(p), "rb") as f: return Response(f.read(), mimetype="application/json")
@app.get("/api/connectome/meta")
def meta():
    p = request.args.get("preset", CFG["connectome"]["default"])
    if not os.path.exists(cpath(p)): return ("not cached", 404)
    with gzip.open(cpath(p), "rt") as f: return jsonify(json.load(f)["meta"])
@app.post("/api/connectome/build")
def do_build():
    p = (request.get_json(silent=True) or {}).get("preset", CFG["connectome"]["default"])
    if p not in CFG["connectome"]["presets"]: return ("bad preset", 400)
    STATE.update(building=True, error=None)
    try:
        m = build(p)
        if not os.path.exists(cxpath()):
            try: build_context()
            except Exception as ex: m["outline_error"] = str(ex)[:200]
        return jsonify(meta=m)
    except Exception as ex: STATE["error"] = str(ex)[:300]; return jsonify(error=STATE["error"]), 500
    finally: STATE["building"] = False
def mlist(): return sorted(glob.glob(os.path.join(MODELS, "model_*.json")))
@app.get("/api/context")
def context():
    if not os.path.exists(cxpath()): return ("not cached", 404)
    with gzip.open(cxpath(), "rb") as f: return Response(f.read(), mimetype="application/json")
@app.post("/api/context/build")
def do_context():
    STATE.update(building=True, error=None)
    try: return jsonify(n=build_context())
    except Exception as ex: STATE["error"] = str(ex)[:300]; return jsonify(error=STATE["error"]), 500
    finally: STATE["building"] = False
@app.get("/api/models")
def models():
    out = []
    for f in mlist():
        with open(f) as fh: m = json.load(fh)
        out.append({k: m.get(k) for k in ("model_id", "experiment_id", "episode", "best", "avg_reward", "saved_at", "connectome_hash", "train_preset", "model_version")})
    return jsonify(out)
@app.post("/api/models/save")
def msave():
    m = request.get_json(force=True); n = len(mlist()) + 1; m["model_id"] = n; m["saved_at"] = time.time()
    os.makedirs(MODELS, exist_ok=True)
    with open(os.path.join(MODELS, f"model_{n:06d}.json"), "w") as f: json.dump(m, f)
    return jsonify(model_id=n)
@app.post("/api/models/load")
def mload():
    n = (request.get_json(force=True) or {}).get("model_id"); fs = mlist()
    f = os.path.join(MODELS, f"model_{int(n):06d}.json") if n else (fs[-1] if fs else None)
    if not f or not os.path.exists(f): return ("no model", 404)
    with open(f) as fh: return Response(fh.read(), mimetype="application/json")
if __name__ == "__main__": app.run(CFG["server"]["host"], CFG["server"]["port"])
