# -*- coding: utf-8 -*-
# Import + execute L2Test217160001 (A-route unit tests), extract Summary verdict.
import json, os, io, sys, subprocess, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

N8N = r"C:\Users\Administrator\AppData\Roaming\npm\n8n.cmd"
WF = r"C:\Users\Administrator\.easyclaw\workspace\n8n-lesson-crew\scripts\wf-21716-l2a-test.json"
WID = "L2Test217160001"
env = dict(os.environ, NODE_FUNCTION_ALLOW_BUILTIN="crypto,fs,path,querystring",
           N8N_RUNNERS_BROKER_PORT="5692")

r = subprocess.run([N8N, "import:workflow", "--input=" + WF], env=env,
                   capture_output=True, text=True, timeout=180)
print("import:", (r.stdout + r.stderr).strip()[-200:])
r = subprocess.run([N8N, "execute", "--id", WID], env=env,
                   capture_output=True, text=True, timeout=600)
out = r.stdout + r.stderr
runs = []
for mm in re.finditer(r'"json": (\{\s*"verdict".*?\})\s*,\s*"pairedItem"', out, re.S):
    try:
        runs.append(json.loads(mm.group(1)))
    except Exception:
        pass
if not runs:
    print("NO SUMMARY FOUND, tail:")
    print(out[-3000:])
    sys.exit(1)
# Summary executes once per arriving branch; merge suites across all runs.
suites = {}
failed = []
for r in runs:
    for s in r["suites"]:
        suites[s["suite"]] = s
    for f in r.get("failed", []):
        if f not in failed:
            failed.append(f)
m = {"verdict": None, "passed": sum(s["passed"] for s in suites.values()),
     "total": sum(s["total"] for s in suites.values()),
     "failed": failed, "suites": list(suites.values())}
m["verdict"] = "ALL_PASS" if m["passed"] == m["total"] else "FAIL"
print("VERDICT:", m["verdict"], "passed %(passed)s/%(total)s" % m)
for s in m["suites"]:
    print("  %(suite)s %(passed)s/%(total)s" % s)
for f in m["failed"]:
    print("  FAIL:", f)
rep = os.path.join(os.path.dirname(WF), "l2a-21716-result.json")
json.dump(m, open(rep, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", rep)