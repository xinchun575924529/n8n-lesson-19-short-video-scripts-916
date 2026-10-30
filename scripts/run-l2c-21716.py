# -*- coding: utf-8 -*-
# Import + execute L2Cstm21716001 (C-route real run), extract Assert output.
import json, os, io, sys, subprocess, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

N8N = r"C:\Users\Administrator\AppData\Roaming\npm\n8n.cmd"
WF = r"C:\Users\Administrator\.easyclaw\workspace\n8n-lesson-crew\workflows\wf-21716-l2c-custom.json"
env = dict(os.environ, NODE_FUNCTION_ALLOW_BUILTIN="crypto,fs,path,querystring",
           N8N_RUNNERS_BROKER_PORT="5694")

r = subprocess.run([N8N, "import:workflow", "--input=" + WF], env=env,
                   capture_output=True, text=True, timeout=180)
print("import:", (r.stdout + r.stderr).strip()[-150:])
r = subprocess.run([N8N, "execute", "--id", "L2Cstm21716001"], env=env,
                   capture_output=True, text=True, timeout=600)
out = r.stdout + r.stderr
found = None
for m2 in re.finditer(r'"json": (\{\s*"scenario": "C".*?\})\s*,\s*"pairedItem"', out, re.S):
    try:
        found = json.loads(m2.group(1))
    except Exception:
        pass
if not found:
    print("NO ASSERT OUTPUT. tail:", out[-2500:])
    sys.exit(1)
print("C => pass %(pass)s/%(total)s" % found)
for it in found["results"]:
    print("  ", "OK " if it.get("pass") else "FAIL", it.get("name"), ("-- " + str(it.get("detail", ""))) if not it.get("pass") else "")
json.dump(found, open(r"C:\Users\Administrator\.easyclaw\workspace\n8n-lesson-crew\state\21716-c-data\c-run-summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)