# -*- coding: utf-8 -*-
# build-l2c-21716.py — L2-C free-route custom workflow for template 21716
# Real chain: draft -> DeepSeek REAL call (OpenAI-compatible) -> SEO kit -> capture
#             render -> Creatomate MOCK -> verify -> capture
#             status -> Creatomate MOCK -> readiness -> capture
# Result written to state\21716-c-data\result.json
import json, os

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(BASE, "workflows", "wf-21716-l2c-custom.json")
DATA = os.path.join(BASE, "state", "21716-c-data")
os.makedirs(DATA, exist_ok=True)
KEY = json.load(open(os.path.join(BASE, "state", "deepseek-key.json"), encoding="utf-8"))["apiKey"]

def node(nid, name, ntype, pos, params, tv=1, extra=None):
    n = {"id": nid, "name": name, "type": ntype, "position": pos, "parameters": params, "typeVersion": tv}
    if extra: n.update(extra)
    return n

def code(nid, name, pos, js, extra=None):
    return node(nid, name, "n8n-nodes-base.code", pos, {"jsCode": js, "mode": "runOnceForAllItems"}, 2, extra)

src = open(os.path.join(os.path.dirname(__file__), "build-l2-test-21716.py"), encoding="utf-8").read()
def extract(tag):
    start = src.index(tag + ' = r"""') + len(tag) + 7
    return src[start:src.index('"""', start)]

V_JS = extract("VALIDATE_JS")
K_JS = extract("SEOKIT_JS")
VR_JS = extract("VERIFY_RENDER_JS")
RD_JS = extract("READINESS_JS")

FEED_DRAFT_JS = r"""
return [{ json: { body: { action: 'draft', topic: 'Why bees are the best pollinators for a small farm', platform: 'youtube', language: 'English', audience: 'backyard beekeepers and small farm owners', tone: 'warm and practical' } } }];
"""

SWITCH_PARAMS = {"rules": {"values": [
    {"outputKey": "Draft", "conditions": {"options": {"leftValue": "", "caseSensitive": False, "typeValidation": "strict"}, "combinator": "and",
        "conditions": [{"id": "c1", "operator": {"type": "string", "operation": "equals"}, "leftValue": "={{ $json.action }}", "rightValue": "draft"}]}, "renameOutput": True},
    {"outputKey": "Render", "conditions": {"options": {"leftValue": "", "caseSensitive": False, "typeValidation": "strict"}, "combinator": "and",
        "conditions": [{"id": "c2", "operator": {"type": "string", "operation": "equals"}, "leftValue": "={{ $json.action }}", "rightValue": "render"}]}, "renameOutput": True},
    {"outputKey": "Status", "conditions": {"options": {"leftValue": "", "caseSensitive": False, "typeValidation": "strict"}, "combinator": "and",
        "conditions": [{"id": "c3", "operator": {"type": "string", "operation": "equals"}, "leftValue": "={{ $json.action }}", "rightValue": "status"}]}, "renameOutput": True},
    {"outputKey": "Audit", "conditions": {"options": {"leftValue": "", "caseSensitive": False, "typeValidation": "strict"}, "combinator": "and",
        "conditions": [{"id": "c4", "operator": {"type": "string", "operation": "equals"}, "leftValue": "={{ $json.action }}", "rightValue": "audit"}]}, "renameOutput": True}]},
    "options": {"fallbackOutput": "extra", "renameFallbackOutput": "Other"}}

# DeepSeek http node — model patched to deepseek-chat via a Code override between Validate and HTTP
PATCH_MODEL_JS = r"""
const v = $input.first().json;
v.requestBody.model = 'deepseek-chat';
if (v.requestBody.messages && v.requestBody.messages[0]) {
  v.requestBody.messages[0].content += ' STRICT LENGTH CONTROL: the voiceover field MUST be 65-100 English words. Count the words before answering; if outside range, rewrite until it fits. This is a hard requirement.';
}
return [{ json: v }];
"""

DEEPSEEK_PARAMS = {
    "url": "https://api.deepseek.com/v1/chat/completions",
    "method": "POST",
    "options": {"timeout": 120000},
    "jsonBody": "={{ JSON.stringify($json.requestBody) }}",
    "sendBody": True,
    "specifyBody": "json",
    "sendHeaders": True,
    "headerParameters": {"parameters": [
        {"name": "Authorization", "value": "Bearer " + KEY},
        {"name": "Content-Type", "value": "application/json"}]}}

SAVE_DRAFT_JS = (r"""
const fs = require('fs');
const v = $input.first().json;
fs.writeFileSync('%s', JSON.stringify(v, null, 2));
return [{ json: v }];
""" % (DATA.replace("\\", "/") + "/draft-result.json"))

# render chain: feed -> validate(render) -> mock creatomate -> verify -> save
FEED_RENDER_JS = r"""
return [{ json: { body: { action: 'render', approved: true, rights_confirmed: true, template_id: 'demo-template-001', hook: 'Bees do the heavy lifting', supporting_text: 'One hive can pollinate a whole small farm.', cta: 'Follow for farm automation' } } }];
"""
MOCK_CREA_POST_JS = "return [{ json: { id: 'c-run-mock-job-001', status: 'planned', url: null } }];"
FEED_STATUS_JS = r"""
return [{ json: { body: { action: 'status', render_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890' } } }];
"""
MOCK_CREA_GET_JS = "return [{ json: { id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', status: 'succeeded', url: 'https://cdn.creatomate/mock-final.mp4', snapshot_url: 'https://cdn.creatomate/mock-snap.jpg' } }];"

SAVE_RAW_JS = SAVE_DRAFT_JS.replace("draft-result.json", "raw-llm.json")

SAVE_RENDER_JS = SAVE_DRAFT_JS.replace("draft-result.json", "render-result.json")
SAVE_STATUS_JS = SAVE_DRAFT_JS.replace("draft-result.json", "status-result.json")

ASSERT_JS = r"""
const fs = require('fs');
const draft = JSON.parse(fs.readFileSync('%DIR%/draft-result.json', 'utf8'));
const render = JSON.parse(fs.readFileSync('%DIR%/render-result.json', 'utf8'));
const status = JSON.parse(fs.readFileSync('%DIR%/status-result.json', 'utf8'));
const checks = [];
checks.push({ name: 'draft ok via DeepSeek real call', pass: draft.ok === true && draft.status === 'draft_ready', detail: JSON.stringify(draft).slice(0, 120) });
checks.push({ name: 'real AI title non-empty <=95', pass: typeof draft.draft?.title === 'string' && draft.draft.title.length > 0 && draft.draft.title.length <= 95, detail: draft.draft && draft.draft.title });
checks.push({ name: 'two distinct hooks', pass: !!draft.draft && draft.draft.hook_a !== draft.draft.hook_b, detail: draft.draft && (draft.draft.hook_a + ' || ' + draft.draft.hook_b) });
checks.push({ name: '4 scenes storyboard', pass: draft.draft?.scenes?.length === 4, detail: String(draft.draft && draft.draft.scenes && draft.draft.scenes.length) });
checks.push({ name: 'voiceover 65-105 words no warning', pass: draft.copy_preflight && draft.copy_preflight.voiceover_length_warning === false, detail: JSON.stringify(draft.copy_preflight) });
checks.push({ name: 'hashtags 3-8 prefixed', pass: Array.isArray(draft.draft?.hashtags) && draft.draft.hashtags.length >= 3 && draft.draft.hashtags.length <= 8 && draft.draft.hashtags.every(h => h[0] === '#'), detail: JSON.stringify(draft.draft && draft.draft.hashtags) });
checks.push({ name: 'publishing kit 3 platforms', pass: !!(draft.publishing_kit?.youtube?.title && draft.publishing_kit?.tiktok?.caption && draft.publishing_kit?.instagram?.caption) });
checks.push({ name: 'topic embedded (bees)', pass: /bee/i.test(JSON.stringify(draft.draft)), detail: draft.draft && draft.draft.title });
checks.push({ name: 'render chain queued (mock creatomate)', pass: render.ok === true && render.status === 'queued' && render.renderId === 'c-run-mock-job-001' });
checks.push({ name: 'status chain succeeded -> videoUrl (mock)', pass: status.ok === true && status.videoUrl === 'https://cdn.creatomate/mock-final.mp4' });
const pass = checks.filter(c => c.pass).length;
return [{ json: { scenario: 'C', pass, total: checks.length, fail: checks.length - pass, results: checks } }];
""".replace("%DIR%", DATA.replace("\\", "/"))

nodes = [
    node("t1", "When Executed by Another Workflow", "n8n-nodes-base.executeWorkflowTrigger", [-1400, 300], {}, 1, {"settings": {}}),
    code("f1", "Feed Draft", [-1200, 140], FEED_DRAFT_JS),
    code("v1", "Validate (draft)", [-1000, 140], V_JS),
    node("sw1", "Route (draft)", "n8n-nodes-base.switch", [-800, 140], SWITCH_PARAMS, 3.2),
    code("pm", "Patch Model to deepseek-chat", [-600, 40], PATCH_MODEL_JS),
    node("ds", "Post to DeepSeek (REAL)", "n8n-nodes-base.httpRequest", [-380, 40], DEEPSEEK_PARAMS, 4.2, {"onError": "continueRegularOutput", "settings": {"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 5000}}),
    code("svr", "Save Raw LLM", [-140, -80], SAVE_RAW_JS),
    code("kit", "Build SEO Kit from Script", [-140, 40], K_JS),
    code("sv1", "Save Draft", [80, 40], SAVE_DRAFT_JS),
    code("f2", "Feed Render", [-1200, 420], FEED_RENDER_JS),
    code("v2", "Validate (render)", [-1000, 420], V_JS),
    node("sw2", "Route (render)", "n8n-nodes-base.switch", [-800, 420], SWITCH_PARAMS, 3.2),
    code("mc", "Post to Creatomate (MOCK)", [-600, 380], MOCK_CREA_POST_JS),
    code("vr", "Verify Render Job Submission", [-380, 380], VR_JS),
    code("sv2", "Save Render", [-140, 380], SAVE_RENDER_JS),
    code("f3", "Feed Status", [-1200, 700], FEED_STATUS_JS),
    code("v3", "Validate (status)", [-1000, 700], V_JS),
    node("sw3", "Route (status)", "n8n-nodes-base.switch", [-800, 700], SWITCH_PARAMS, 3.2),
    code("mg", "Fetch Creatomate Status (MOCK)", [-600, 660], MOCK_CREA_GET_JS),
    code("rd", "Check Video Readiness", [-380, 660], RD_JS),
    code("sv3", "Save Status", [-140, 660], SAVE_STATUS_JS),
    code("asrt", "Assert C Run", [300, 380], ASSERT_JS),
]

conns = {}
def add(s, d, o=0):
    c = conns.setdefault(s, {"main": []})
    while len(c["main"]) <= o: c["main"].append([])
    c["main"][o].append({"node": d, "type": "main", "index": 0})

add("When Executed by Another Workflow", "Feed Draft")
add("When Executed by Another Workflow", "Feed Render")
add("When Executed by Another Workflow", "Feed Status")
add("Feed Draft", "Validate (draft)"); add("Validate (draft)", "Route (draft)")
add("Route (draft)", "Patch Model to deepseek-chat", 0)
add("Patch Model to deepseek-chat", "Post to DeepSeek (REAL)")
add("Post to DeepSeek (REAL)", "Save Raw LLM")
add("Post to DeepSeek (REAL)", "Build SEO Kit from Script")
add("Build SEO Kit from Script", "Save Draft")
add("Feed Render", "Validate (render)"); add("Validate (render)", "Route (render)")
add("Route (render)", "Post to Creatomate (MOCK)", 1)
add("Post to Creatomate (MOCK)", "Verify Render Job Submission")
add("Verify Render Job Submission", "Save Render")
add("Feed Status", "Validate (status)"); add("Validate (status)", "Route (status)")
add("Route (status)", "Fetch Creatomate Status (MOCK)", 2)
add("Fetch Creatomate Status (MOCK)", "Check Video Readiness")
add("Check Video Readiness", "Save Status")
add("Save Draft", "Assert C Run")
add("Save Render", "Assert C Run")
add("Save Status", "Assert C Run")

wf = {"id": "L2Cstm21716001", "name": "L2Cstm21716001", "nodes": nodes,
      "connections": conns, "settings": {}, "pinData": {}}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(wf, f, ensure_ascii=False, indent=1)
print("written", OUT, len(nodes), "nodes")