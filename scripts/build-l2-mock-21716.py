# -*- coding: utf-8 -*-
# build-l2-mock-21716.py — L2-B mock full-chain generator for template 21716
# Keeps template structure (Validate -> Switch -> branch) with externals mocked:
#   webhook trigger -> executeWorkflowTrigger + Code fixture
#   Post to OpenAI -> Fake OpenAI (Code)
#   Post/Fetch Creatomate -> Fake Creatomate (Code)
#   respondToWebhook -> Capture Response (Code, replicates responseCode expr)
import json, os

DIR = os.path.join(os.path.dirname(__file__), "..", "workflows", "l2-mock-21716")
os.makedirs(DIR, exist_ok=True)

def node(nid, name, ntype, pos, params, tv=1, extra=None):
    n = {"id": nid, "name": name, "type": ntype, "position": pos, "parameters": params, "typeVersion": tv}
    if extra: n.update(extra)
    return n

def code(nid, name, pos, js, extra=None):
    return node(nid, name, "n8n-nodes-base.code", pos, {"jsCode": js, "mode": "runOnceForAllItems"}, 2, extra)

VALIDATE_JS = open(os.path.join(os.path.dirname(__file__), "build-l2-test-21716.py"), encoding="utf-8").read()
# extract verbatim blocks from the A-route generator to guarantee fidelity
def extract(tag):
    src = VALIDATE_JS
    start = src.index(tag + ' = r"""') + len(tag) + 7
    end = src.index('"""', start)
    return src[start:end]

V_JS = extract("VALIDATE_JS")
K_JS = extract("SEOKIT_JS")
VR_JS = extract("VERIFY_RENDER_JS")
RD_JS = extract("READINESS_JS")
N_JS = extract("NORMALIZE_JS")
PF_JS = extract("PREFLIGHT_JS")

# Switch node — verbatim from template
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

CAPTURE_JS = r"""
const v = $input.first().json;
const code = v.ok ? 200 : (v.errorCode === 'validation' ? 400 : 502);
return [{ json: { httpCode: code, body: v } }];
"""

GOOD_SCRIPT = {
    "title": "Automate shorts with n8n in 3 steps",
    "hook_a": "You are editing shorts by hand?",
    "hook_b": "This robot writes your script",
    "supporting_text": "n8n + AI writes the script, you only review.",
    "cta": "Follow for more automation",
    "description": "Full workflow breakdown for short-form automation.",
    "voiceover": " ".join(["word"] * 72),
    "hashtags": ["n8n", "automation", "shorts"],
    "seo_keywords": ["n8n shorts", "ai video"],
    "scenes": [{"on_screen_text": "s%d" % i, "visual_direction": "v%d" % i, "voiceover_line": "l%d" % i} for i in range(1, 5)],
}
FAKE_OPENAI_JS = "return [{ json: { choices: [{ finish_reason: 'stop', message: { content: %s } }] } }];" % json.dumps(json.dumps(GOOD_SCRIPT))
FAKE_OPENAI_ERR_JS = "return [{ json: { error: 'rate limit exceeded' } }];"
FAKE_CREA_POST_JS = "return [{ json: { id: 'job-abc-001', status: 'planned', url: null } }];"
FAKE_CREA_OK_JS = "return [{ json: { id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', status: 'succeeded', url: 'https://cdn.creatomate/final.mp4', snapshot_url: 'https://cdn.creatomate/snap.jpg' } }];"
FAKE_CREA_FAIL_JS = "return [{ json: { id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', status: 'failed', errors: ['font missing'] } }];"

def build_scenario(sid, feed_body, branch, externals, asserts):
    """branch: draft|render|status|audit|other ; externals: dict name->js"""
    nodes = [node("t1", "When Executed by Another Workflow", "n8n-nodes-base.executeWorkflowTrigger", [-1400, 300], {}, 1, {"settings": {}}),
             code("feed", "Feed Webhook Body", [-1200, 300], "return [{ json: %s }];" % json.dumps({"body": feed_body}, ensure_ascii=False)),
             code("val", "Check Action and Budget Validity", [-950, 300], V_JS),
             node("sw", "Route by Video Task", "n8n-nodes-base.switch", [-700, 300], SWITCH_PARAMS, 3.2)]
    conns = {}
    def add(s, d, o=0):
        c = conns.setdefault(s, {"main": []})
        while len(c["main"]) <= o: c["main"].append([])
        c["main"][o].append({"node": d, "type": "main", "index": 0})
    add("When Executed by Another Workflow", "Feed Webhook Body")
    add("Feed Webhook Body", "Check Action and Budget Validity")
    add("Check Action and Budget Validity", "Route by Video Task")

    # branch chains: (switch out idx, first node, chain...)
    if branch == "draft":
        ext = externals.get("openai", FAKE_OPENAI_JS)
        nodes += [code("oai", "Post to OpenAI (MOCK)", [-450, 140], ext),
                  code("kit", "Build SEO Kit from Script", [-200, 140], K_JS),
                  code("cap", "Capture Response", [50, 140], CAPTURE_JS),
                  code("asrt", "Assert Scenario", [300, 140], asserts)]
        add("Route by Video Task", "Post to OpenAI (MOCK)", 0)
        add("Post to OpenAI (MOCK)", "Build SEO Kit from Script")
        add("Build SEO Kit from Script", "Capture Response")
        add("Capture Response", "Assert Scenario")
    elif branch == "render":
        ext = externals.get("crea_post", FAKE_CREA_POST_JS)
        nodes += [code("cp", "Post to Creatomate (MOCK)", [-450, 300], ext),
                  code("vr", "Verify Render Job Submission", [-200, 300], VR_JS),
                  code("cap", "Capture Response", [50, 300], CAPTURE_JS),
                  code("asrt", "Assert Scenario", [300, 300], asserts)]
        add("Route by Video Task", "Post to Creatomate (MOCK)", 1)
        add("Post to Creatomate (MOCK)", "Verify Render Job Submission")
        add("Verify Render Job Submission", "Capture Response")
        add("Capture Response", "Assert Scenario")
    elif branch == "status":
        ext = externals.get("crea_get", FAKE_CREA_OK_JS)
        nodes += [code("cg", "Fetch Creatomate Render Status (MOCK)", [-450, 460], ext),
                  code("rd", "Check Video Readiness", [-200, 460], RD_JS),
                  code("cap", "Capture Response", [50, 460], CAPTURE_JS),
                  code("asrt", "Assert Scenario", [300, 460], asserts)]
        add("Route by Video Task", "Fetch Creatomate Render Status (MOCK)", 2)
        add("Fetch Creatomate Render Status (MOCK)", "Check Video Readiness")
        add("Check Video Readiness", "Capture Response")
        add("Capture Response", "Assert Scenario")
    elif branch == "audit":
        nodes += [code("pf", "Execute Preflight Script Check", [-450, 620], PF_JS),
                  code("cap", "Capture Response", [-200, 620], CAPTURE_JS),
                  code("asrt", "Assert Scenario", [50, 620], asserts)]
        add("Route by Video Task", "Execute Preflight Script Check", 3)
        add("Execute Preflight Script Check", "Capture Response")
        add("Capture Response", "Assert Scenario")
    else:  # other
        nodes += [code("nm", "Handle and Normalize Input Errors", [-450, 780], N_JS),
                  code("cap", "Capture Response", [-200, 780], CAPTURE_JS),
                  code("asrt", "Assert Scenario", [50, 780], asserts)]
        add("Route by Video Task", "Handle and Normalize Input Errors", 4)
        add("Handle and Normalize Input Errors", "Capture Response")
        add("Capture Response", "Assert Scenario")

    wf = {"id": "L2Mock21716%s01" % sid, "name": "L2Mock21716%s01" % sid,
          "nodes": nodes, "connections": conns, "settings": {}, "pinData": {}}
    path = os.path.join(DIR, "wf-mock-21716-%s.json" % sid)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)
    print("written", path, len(nodes), "nodes")

def A(scenario, checks):
    lines = ["const v = $input.first().json; const checks = [];"]
    for name, expr, got in checks:
        l = "checks.push({ name: %s, pass: !!(%s)" % (json.dumps(name, ensure_ascii=False), expr)
        if got: l += ", detail: String(%s)" % got
        l += " });"
        lines.append(l)
    lines.append("const pass = checks.filter(c=>c.pass).length, fail = checks.length - pass;")
    lines.append("return [{ json: { scenario: %s, pass, total: checks.length, fail, results: checks } }];" % json.dumps(scenario))
    return "\n".join(lines)

UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# S1 draft full success
build_scenario("S1", {"action": "draft", "topic": "How to automate shorts with n8n", "platform": "youtube", "audience": "creators", "tone": "clear"}, "draft", {}, A("S1", [
    ("route hit draft branch -> http 200", "v.httpCode === 200", "v.httpCode"),
    ("status draft_ready", "v.body.status === 'draft_ready'", "JSON.stringify(v.body).slice(0,80)"),
    ("title carried from AI", "v.body.draft.title === 'Automate shorts with n8n in 3 steps'", None),
    ("4 storyboard scenes", "v.body.draft.scenes.length === 4", None),
    ("hashtags prefixed", "v.body.draft.hashtags[0] === '#n8n'", None),
    ("publishing kit has youtube/tiktok/instagram", "!!(v.body.publishing_kit.youtube && v.body.publishing_kit.tiktok && v.body.publishing_kit.instagram)", None),
    ("preflight words=72 no warn", "v.body.copy_preflight.words === 72 && v.body.copy_preflight.voiceover_length_warning === false", None)]))

# S2 render success (double gate approved)
build_scenario("S2", {"action": "render", "approved": True, "rights_confirmed": True, "template_id": "abc-123-template", "hook": "Big hook", "supporting_text": "support", "cta": "Follow"}, "render", {}, A("S2", [
    ("http 200", "v.httpCode === 200", "v.httpCode"),
    ("status queued + renderId", "v.body.status === 'queued' && v.body.renderId === 'job-abc-001'", "JSON.stringify(v.body).slice(0,120)"),
    ("async warning present", "/asynchronous/.test(v.body.warning)", None)]))

# S3 status succeeded -> video url
build_scenario("S3", {"action": "status", "render_id": UUID}, "status", {}, A("S3", [
    ("http 200", "v.httpCode === 200", None),
    ("videoUrl returned", "v.body.videoUrl === 'https://cdn.creatomate/final.mp4'", "JSON.stringify(v.body).slice(0,120)"),
    ("snapshotUrl returned", "v.body.snapshotUrl === 'https://cdn.creatomate/snap.jpg'", None),
    ("ready message", "/Video ready/.test(v.body.message)", None)]))

# S4 status failed -> ok:false -> 502
build_scenario("S4", {"action": "status", "render_id": UUID}, "status", {"crea_get": FAKE_CREA_FAIL_JS}, A("S4", [
    ("http 502 (ok false, not validation)", "v.httpCode === 502", "v.httpCode"),
    ("errors carried", "v.body.errors[0] === 'font missing'", None),
    ("videoUrl null", "v.body.videoUrl === null", None)]))

# S5 audit -> preflight 200
build_scenario("S5", {"action": "audit", "title": "3 tricks", "hook": "Stop scrolling", "voiceover": " ".join(["w"] * 80)}, "audit", {}, A("S5", [
    ("http 200", "v.httpCode === 200", None),
    ("audit_ready", "v.body.status === 'audit_ready'", None),
    ("spoken_words 80, no warnings", "v.body.audit.spoken_words === 80 && v.body.audit.warnings.length === 0", "JSON.stringify(v.body).slice(0,140)")]))

# E1 unknown action -> Other -> 400
build_scenario("E1", {"action": "delete"}, "other", {}, A("E1", [
    ("fallback Other branch -> 400", "v.httpCode === 400", "v.httpCode"),
    ("validation error enum msg", "/draft, audit, render or status/.test(v.body.error)", "v.body.error")]))

# E2 draft topic too short -> validation fail -> Other -> 400
build_scenario("E2", {"action": "draft", "topic": "ab"}, "other", {}, A("E2", [
    ("http 400", "v.httpCode === 400", "v.httpCode"),
    ("topic length msg", "/5–400/.test(v.body.error)", "v.body.error")]))

# E3 render without approvals -> Other -> 400
build_scenario("E3", {"action": "render", "approved": False, "rights_confirmed": False, "template_id": "abc-123-template", "hook": "h", "supporting_text": "s", "cta": "c"}, "other", {}, A("E3", [
    ("http 400", "v.httpCode === 400", "v.httpCode"),
    ("approval gate msg", "/approved=true and rights_confirmed=true/.test(v.body.error)", "v.body.error")]))

# E4 draft with OpenAI error -> draft branch -> seokit ok:false -> 502
build_scenario("E4", {"action": "draft", "topic": "perfectly fine topic here"}, "draft", {"openai": FAKE_OPENAI_ERR_JS}, A("E4", [
    ("http 502", "v.httpCode === 502", "v.httpCode"),
    ("upstream errorCode", "v.body.errorCode === 'upstream'", "JSON.stringify(v.body).slice(0,120)")]))

print("all scenarios built in", DIR)