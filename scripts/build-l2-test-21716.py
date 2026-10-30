# -*- coding: utf-8 -*-
# build-l2-test-21716.py v2 — L2-A unit test workflow generator for template 21716
# Structure: one branch per case (feed 1 item -> verbatim unit code -> case assert)
# because template code uses $input.first() in runOnceForAllItems mode.
import json, os

OUT = os.path.join(os.path.dirname(__file__), "wf-21716-l2a-test.json")

def node(nid, name, ntype, pos, params, tv=1, extra=None):
    n = {"id": nid, "name": name, "type": ntype, "position": pos, "parameters": params, "typeVersion": tv}
    if extra: n.update(extra)
    return n

def code(nid, name, pos, js, extra=None):
    return node(nid, name, "n8n-nodes-base.code", pos, {"jsCode": js, "mode": "runOnceForAllItems"}, 2, extra)

# ---------------- verbatim template logic (6 Code nodes) ----------------

VALIDATE_JS = r"""
const b=$input.first().json.body||{}, action=String(b.action||'').trim().toLowerCase();
const fail=s=>[{json:{ok:false,action:'invalid',errorCode:'validation',error:s}}];
const clean=(v,max=1400)=>String(v||'').trim().slice(0,max);
if(action==='draft'){
  const topic=clean(b.topic,401), language=clean(b.language||'English',40);
  const platform=['youtube','tiktok','instagram'].includes(String(b.platform||'').toLowerCase())?String(b.platform).toLowerCase():'youtube';
  const audience=clean(b.audience||'general audience',100), tone=clean(b.tone||'engaging and clear',80);
  if(topic.length<5||topic.length>400)return fail('topic must contain 5–400 characters');
  if(!language||!audience||!tone)return fail('language/audience/tone cannot be blank');
  const messages=[
    {role:'system',content:'You create ORIGINAL factuality-conscious 9:16 short-form video content. Return ONLY a JSON object with nonempty string keys title,hook_a,hook_b,supporting_text,cta,description,voiceover and arrays hashtags,seo_keywords,scenes. Exactly 4 scenes, each with on_screen_text,visual_direction,voiceover_line (all strings). Target 25–45 seconds and 65–105 spoken words. Suggest only footage the user owns or has licensed. No fabricated claims, fake testimonials, copied scripts, unsafe sensationalism or copyrighted music. Captions concise. Title <=95 chars. Hooks distinct. Hashtags 3–8. Avoid implying this content is fact-checked, trending or guaranteed viral.'},
    {role:'user',content:`Topic: ${topic}\nLanguage: ${language}\nPlatform: ${platform}\nAudience: ${audience}\nStyle: ${tone}\nCreate two alternative hooks and a shot-by-shot storyboard, voiceover and platform-specific metadata.`}
  ];
  return [{json:{action:'draft',ok:true,platform,topic,requestBody:{model:'gpt-4o-mini',temperature:0.65,response_format:{type:'json_object'},messages}}}];
}
if(action==='audit'){
  const title=clean(b.title,150),hook=clean(b.hook,240),voiceover=clean(b.voiceover,5000);
  if(!title||!hook||!voiceover)return fail('audit requires title, hook and voiceover');
  const words=voiceover.split(/\s+/).filter(Boolean).length,duration=Math.round(words/2.5),warnings=[];
  if(title.length>95)warnings.push('Title exceeds suggested 95-character limit');
  if(words<65||words>105)warnings.push('Voiceover may not fit a 25–45 second short');
  if(/guaranteed|100% guaranteed|miracle cure|اغتنم الفرصة مضمونة/i.test(title+' '+voiceover))warnings.push('Review absolute or exaggerated claims');
  if(hook.trim().toLowerCase()===title.trim().toLowerCase())warnings.push('Hook and title are identical; test distinct openings');
  return [{json:{action:'audit',ok:true,route:'audit',audit:{spoken_words:words,estimated_duration_sec:duration,warnings,manual_checks:['Verify factual claims and sources','Check music, footage, voice and image licenses','Review subtitles, accessibility and platform terms','Confirm brand safety before paid render'],passed_basic_copy_checks:warnings.length===0},note:'This is a deterministic copy preflight, not fact-checking or copyright clearance.'}}];
}
if(action==='render'){
  const templateId=clean(b.template_id,120),hook=clean(b.hook,200),support=clean(b.supporting_text,1500),cta=clean(b.cta,200);
  if(b.approved!==true||b.rights_confirmed!==true)return fail('render requires approved=true and rights_confirmed=true after human review');
  if(!/^[a-zA-Z0-9-]{10,100}$/.test(templateId))return fail('Provide a real Creatomate template_id');
  if(!hook||hook.length>160||!support||support.length>1200||!cta||cta.length>160)return fail('Provide valid hook, supporting_text and cta');
  return [{json:{action:'render',ok:true,requestBody:{template_id:templateId,modifications:{Hook:hook,Supporting_Text:support,CTA:cta},max_width:1080,max_height:1920}}}];
}
if(action==='status'){
  const renderId=clean(b.render_id,60);
  if(!/^[0-9a-fA-F-]{30,45}$/.test(renderId))return fail('render_id must be a Creatomate UUID-like ID');
  return [{json:{action:'status',ok:true,renderId}}];
}
return fail('action must be draft, audit, render or status');
"""

SEOKIT_JS = r"""
const v=$input.first().json;
if(v.error||v.choices?.[0]?.finish_reason==='length')return [{json:{ok:false,errorCode:'upstream',error:'AI request failed or returned truncated content'}}];
try{
 const raw=v.choices?.[0]?.message?.content;const d=JSON.parse(raw);
 for(const k of ['title','hook_a','hook_b','supporting_text','cta','description','voiceover'])if(typeof d[k]!=='string'||!d[k].trim())throw Error('missing '+k);
 if(!Array.isArray(d.scenes)||d.scenes.length!==4)throw Error('expected four storyboard scenes');
 for(const s of d.scenes)for(const k of ['on_screen_text','visual_direction','voiceover_line'])if(typeof s[k]!=='string'||!s[k].trim())throw Error('scene missing '+k);
 const trim=(v,n)=>String(v).trim().slice(0,n);
 const hash=(Array.isArray(d.hashtags)?d.hashtags:[]).map(h=>('#'+String(h).replace(/^#+/,'').replace(/[^\p{L}\p{N}_]/gu,'')).slice(0,40)).filter(x=>x.length>1).slice(0,8);
 const kw=(Array.isArray(d.seo_keywords)?d.seo_keywords:[]).map(x=>trim(x,60)).filter(Boolean).slice(0,12);
 const words=d.voiceover.trim().split(/\s+/).length;
 const title=trim(d.title,95), description=trim(d.description,1000);
 const kit={youtube:{title,description:description+'\n'+hash.join(' ')},tiktok:{caption:trim(description,300)+' '+hash.join(' ')},instagram:{caption:trim(description,500)+'\n'+hash.join(' ')},keywords:kw};
 return [{json:{ok:true,status:'draft_ready',requires_review:true,creator:'TYKAIRO-AI',draft:{title,hook_a:trim(d.hook_a,110),hook_b:trim(d.hook_b,110),supporting_text:trim(d.supporting_text,1200),cta:trim(d.cta,160),voiceover:trim(d.voiceover,1400),scenes:d.scenes.map((s,i)=>({shot:i+1,on_screen_text:trim(s.on_screen_text,150),visual_direction:trim(s.visual_direction,350),voiceover_line:trim(s.voiceover_line,260)})),hashtags:hash,seo_keywords:kw},publishing_kit:kit,copy_preflight:{words,approx_seconds:Math.round(words/2.5),voiceover_length_warning:words<65||words>105},next_action:'Review scripts and rights; optionally action=audit; then action=render with explicit approvals. Publishing is manual.'}}];
}catch(e){return [{json:{ok:false,errorCode:'upstream',error:'Invalid AI script schema: '+String(e.message).slice(0,130)}}];}
"""

VERIFY_RENDER_JS = r"""
const v=$input.first().json;
if(v.error||!v.id)return [{json:{ok:false,errorCode:'upstream',error:'Creatomate did not accept the render job',details:String(v.hint||v.error||'').slice(0,120)}}];
return [{json:{ok:true,status:'queued',renderId:v.id,renderStatus:v.status||'planned',renderUrl:v.url||null,warning:'Rendering is asynchronous. Use action=status with render_id to check readiness.'}}];
"""

READINESS_JS = r"""
const v=$input.first().json;
if(v.error||!v.id)return [{json:{ok:false,errorCode:'upstream',error:'Could not retrieve render status; check credentials and job ID'}}];
const status=v.status||'unknown';return [{json:{ok:status!=='failed',status,renderId:v.id,videoUrl:status==='succeeded'?v.url:null,snapshotUrl:status==='succeeded'?(v.snapshot_url||null):null,errors:Array.isArray(v.errors)?v.errors:[],message:status==='succeeded'?'Video ready. Review visually before manual publishing.':status==='failed'?'Render failed: review Creatomate job errors.':'Video still processing; request status later.'}}];
"""

NORMALIZE_JS = r"""
return [{json:{ok:false,errorCode:'validation',error:$input.first().json.error||'Unknown action'}}];
"""

PREFLIGHT_JS = r"""
const v=$input.first().json;
return [{json:{ok:true,status:'audit_ready',audit:v.audit,note:v.note}}];
"""

UNITS = {
    "validate": VALIDATE_JS,
    "seokit": SEOKIT_JS,
    "verify": VERIFY_RENDER_JS,
    "ready": READINESS_JS,
    "norm": NORMALIZE_JS,
    "preflight": PREFLIGHT_JS,
}

GOOD_SCRIPT = {
    "title": "Hook title that is safely under the limit",
    "hook_a": "Hook A " + "x" * 130,
    "hook_b": "Hook B",
    "supporting_text": "support " + "y" * 1300,
    "cta": "follow us",
    "description": "desc " + "z" * 1100,
    "voiceover": " ".join(["voice"] * 70),
    "hashtags": ["#n8n", "##double#hash", "bad tag!", "automation"],
    "seo_keywords": ["n8n shorts", "k" * 80, ""],
    "scenes": [{"on_screen_text": "s%d" % i, "visual_direction": "v%d" % i, "voiceover_line": "l%d" % i} for i in range(1, 5)],
}
def oai(content): return {"choices": [{"finish_reason": "stop", "message": {"content": content}}]}
SC4 = [{"on_screen_text": "s", "visual_direction": "v", "voiceover_line": "l"}] * 4

# (case_name, unit, input_json, [(assert_name, js_expr_bool_with_r, got_expr_or_None), ...])
CASES = [
 ("draft-ok", "validate", {"body": {"action": "Draft", "topic": "How n8n automates short video scripts", "platform": "TiKTok", "audience": "solo creators", "tone": "punchy"}}, [
    ("action lowercased to draft", "r.action === 'draft'", "r.action"),
    ("ok true", "r.ok === true", None),
    ("platform case-insensitive tiktok kept", "r.platform === 'tiktok'", "r.platform"),
    ("model pinned gpt-4o-mini", "r.requestBody.model === 'gpt-4o-mini'", None),
    ("temperature 0.65", "r.requestBody.temperature === 0.65", None),
    ("response_format json_object", "r.requestBody.response_format && r.requestBody.response_format.type === 'json_object'", None),
    ("messages [system,user]", "r.requestBody.messages.length === 2 && r.requestBody.messages[0].role === 'system' && r.requestBody.messages[1].role === 'user'", None),
    ("system prompt requires exactly 4 scenes", "/Exactly 4 scenes/.test(r.requestBody.messages[0].content)", None),
    ("user prompt embeds topic/platform/tone", "/How n8n automates/.test(r.requestBody.messages[1].content) && /Platform: tiktok/.test(r.requestBody.messages[1].content) && /punchy/.test(r.requestBody.messages[1].content)", None)]),
 ("draft-defaults", "validate", {"body": {"action": "draft", "topic": "Minimal topic only here"}}, [
    ("platform defaults youtube", "r.platform === 'youtube'", "r.platform"),
    ("language default English", "/Language: English/.test(r.requestBody.messages[1].content)", None),
    ("audience default", "/Audience: general audience/.test(r.requestBody.messages[1].content)", None),
    ("tone default", "/Style: engaging and clear/.test(r.requestBody.messages[1].content)", None)]),
 ("draft-topic-short", "validate", {"body": {"action": "draft", "topic": "ab"}}, [
    ("topic <5 -> validation fail", "r.ok === false && r.errorCode === 'validation' && /5–400/.test(r.error)", "r.error"),
    ("fail sets action invalid", "r.action === 'invalid'", None)]),
 ("draft-topic-long", "validate", {"body": {"action": "draft", "topic": "x" * 401}}, [
    ("topic 401 chars -> fail", "r.ok === false && /5–400/.test(r.error)", "r.error")]),
 ("draft-lang-blank", "validate", {"body": {"action": "draft", "topic": "perfectly fine topic", "language": "   "}}, [
    ("blank language after trim -> fail", "r.ok === false && /language/.test(r.error)", "r.error")]),
 ("draft-platform-illegal", "validate", {"body": {"action": "draft", "topic": "decent length topic here", "platform": "linkedin"}}, [
    ("illegal platform silently defaults youtube (documented)", "r.ok === true && r.platform === 'youtube'", "r.platform")]),
 ("audit-ok", "validate", {"body": {"action": "audit", "title": "3 n8n tricks for shorts", "hook": "Stop wasting hours editing", "voiceover": " ".join(["word"] * 80)}}, [
    ("audit ok", "r.ok === true && r.action === 'audit'", None),
    ("spoken_words 80", "r.audit.spoken_words === 80", "r.audit && r.audit.spoken_words"),
    ("duration 80/2.5=32s", "r.audit.estimated_duration_sec === 32", None),
    ("zero warnings -> passed true", "r.audit.warnings.length === 0 && r.audit.passed_basic_copy_checks === true", None),
    ("4 manual checks", "r.audit.manual_checks.length === 4", None),
    ("deterministic note", "/not fact-checking/.test(r.note)", None)]),
 ("audit-title-long", "validate", {"body": {"action": "audit", "title": "x" * 96, "hook": "different hook", "voiceover": " ".join(["w"] * 80)}}, [
    ("title >95 warns", "r.audit.warnings.some(w => /95-character/.test(w))", "JSON.stringify(r.audit&&r.audit.warnings)")]),
 ("audit-words-few", "validate", {"body": {"action": "audit", "title": "fine title", "hook": "fine hook", "voiceover": "too few words"}}, [
    ("voiceover <65 words warns", "r.audit.warnings.some(w => /25–45 second/.test(w))", None),
    ("passed false when warnings", "r.audit.passed_basic_copy_checks === false", None)]),
 ("audit-words-many", "validate", {"body": {"action": "audit", "title": "fine title", "hook": "fine hook", "voiceover": " ".join(["w"] * 120)}}, [
    ("voiceover >105 words warns", "r.audit.warnings.some(w => /25–45 second/.test(w))", None)]),
 ("audit-hook-eq-title", "validate", {"body": {"action": "audit", "title": "Same Thing", "hook": "same thing", "voiceover": " ".join(["w"] * 80)}}, [
    ("hook==title case-insensitive warns", "r.audit.warnings.some(w => /identical/.test(w))", None)]),
 ("audit-guaranteed", "validate", {"body": {"action": "audit", "title": "This is 100% guaranteed to work", "hook": "wow", "voiceover": " ".join(["w"] * 80)}}, [
    ("100% guaranteed flagged", "r.audit.warnings.some(w => /absolute or exaggerated/.test(w))", None)]),
 ("audit-arabic", "validate", {"body": {"action": "audit", "title": "عنوان", "hook": "خطاف", "voiceover": " ".join(["كلمة"] * 80) + " اغتنم الفرصة مضمونة"}}, [
    ("Arabic absolute-claim regex flagged", "r.audit.warnings.some(w => /absolute or exaggerated/.test(w))", "JSON.stringify(r.audit&&r.audit.warnings)")]),
 ("audit-missing-fields", "validate", {"body": {"action": "audit", "title": "only title"}}, [
    ("audit missing hook+voiceover -> fail", "r.ok === false && /title, hook and voiceover/.test(r.error)", "r.error")]),
 ("render-ok", "validate", {"body": {"action": "render", "approved": True, "rights_confirmed": True, "template_id": "abc-123-template", "hook": "Big hook", "supporting_text": "support body", "cta": "Follow for more"}}, [
    ("render ok", "r.ok === true && r.action === 'render'", None),
    ("template_id carried", "r.requestBody.template_id === 'abc-123-template'", None),
    ("modifications Hook/Supporting_Text/CTA", "r.requestBody.modifications.Hook === 'Big hook' && r.requestBody.modifications.Supporting_Text === 'support body' && r.requestBody.modifications.CTA === 'Follow for more'", None),
    ("1080x1920 9:16", "r.requestBody.max_width === 1080 && r.requestBody.max_height === 1920", None)]),
 ("render-no-rights", "validate", {"body": {"action": "render", "approved": True, "rights_confirmed": False, "template_id": "abc-123-template", "hook": "h", "supporting_text": "s", "cta": "c"}}, [
    ("rights_confirmed=false blocked", "r.ok === false && /approved=true and rights_confirmed=true/.test(r.error)", "r.error")]),
 ("render-approved-string", "validate", {"body": {"action": "render", "approved": "true", "rights_confirmed": True, "template_id": "abc-123-template", "hook": "h", "supporting_text": "s", "cta": "c"}}, [
    ("approved string 'true' blocked (strict ===)", "r.ok === false", "r.error")]),
 ("render-bad-template", "validate", {"body": {"action": "render", "approved": True, "rights_confirmed": True, "template_id": "short", "hook": "h", "supporting_text": "s", "cta": "c"}}, [
    ("template_id <10 chars blocked", "r.ok === false && /template_id/.test(r.error)", "r.error")]),
 ("render-hook-long", "validate", {"body": {"action": "render", "approved": True, "rights_confirmed": True, "template_id": "abc-123-template", "hook": "x" * 161, "supporting_text": "s", "cta": "c"}}, [
    ("hook >160 blocked", "r.ok === false && /hook, supporting_text and cta/.test(r.error)", "r.error")]),
 ("render-support-empty", "validate", {"body": {"action": "render", "approved": True, "rights_confirmed": True, "template_id": "abc-123-template", "hook": "h", "supporting_text": "", "cta": "c"}}, [
    ("empty supporting_text blocked", "r.ok === false", "r.error")]),
 ("status-ok", "validate", {"body": {"action": "status", "render_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}}, [
    ("status ok + renderId passthrough", "r.ok === true && r.action === 'status' && r.renderId === 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'", None)]),
 ("status-bad-uuid", "validate", {"body": {"action": "status", "render_id": "not-a-uuid"}}, [
    ("bad render_id rejected", "r.ok === false && /UUID-like/.test(r.error)", "r.error")]),
 ("status-missing", "validate", {"body": {"action": "status"}}, [
    ("missing render_id rejected", "r.ok === false", "r.error")]),
 ("unknown-action", "validate", {"body": {"action": "delete"}}, [
    ("unknown action rejected with enum msg", "r.ok === false && /draft, audit, render or status/.test(r.error)", "r.error")]),
 ("no-action", "validate", {"body": {}}, [
    ("missing action rejected", "r.ok === false", "r.error")]),
 ("seokit-ok", "seokit", oai(json.dumps(GOOD_SCRIPT)), [
    ("ok + draft_ready + requires_review", "r.ok === true && r.status === 'draft_ready' && r.requires_review === true", None),
    ("creator TYKAIRO-AI", "r.creator === 'TYKAIRO-AI'", None),
    ("hook_a truncated to 110", "r.draft.hook_a.length === 110", "r.draft && r.draft.hook_a && r.draft.hook_a.length"),
    ("supporting_text truncated 1200", "r.draft.supporting_text.length === 1200", None),
    ("youtube desc first line = description truncated 1000", "r.publishing_kit.youtube.description.split('\\n')[0].length === 1000", "r.publishing_kit && r.publishing_kit.youtube.description.split('\\n')[0].length"),
    ("##double#hash -> #doublehash", "r.draft.hashtags.includes('#doublehash')", "JSON.stringify(r.draft&&r.draft.hashtags)"),
    ("bad tag! -> #badtag", "r.draft.hashtags.includes('#badtag')", None),
    ("#n8n kept first", "r.draft.hashtags[0] === '#n8n'", None),
    ("seo_keywords trimmed 60, empty dropped", "r.draft.seo_keywords.length === 2 && r.draft.seo_keywords[1].length === 60", "JSON.stringify(r.draft&&r.draft.seo_keywords)"),
    ("4 scenes shot 1..4", "r.draft.scenes.length === 4 && r.draft.scenes[0].shot === 1 && r.draft.scenes[3].shot === 4", None),
    ("preflight words=70 ~28s no warn", "r.copy_preflight.words === 70 && r.copy_preflight.approx_seconds === 28 && r.copy_preflight.voiceover_length_warning === false", "JSON.stringify(r.copy_preflight)"),
    ("youtube kit title + hashtags", "r.publishing_kit.youtube.title === r.draft.title && /#n8n/.test(r.publishing_kit.youtube.description)", None),
    ("tiktok caption single-line", "r.publishing_kit.tiktok.caption.indexOf('\\n') === -1", None),
    ("next_action manual publishing", "/Publishing is manual/.test(r.next_action)", None)]),
 ("seokit-err-v.error", "seokit", {"error": "rate limit"}, [
    ("v.error -> upstream", "r.ok === false && r.errorCode === 'upstream'", None)]),
 ("seokit-err-truncated", "seokit", {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}, [
    ("finish_reason=length -> truncated error", "r.ok === false && /truncated/.test(r.error)", "r.error")]),
 ("seokit-err-badjson", "seokit", oai("not json at all"), [
    ("invalid JSON -> schema error", "r.ok === false && /Invalid AI script schema/.test(r.error)", "r.error")]),
 ("seokit-err-scenes", "seokit", oai(json.dumps({"title": "t", "hook_a": "a", "hook_b": "b", "supporting_text": "s", "cta": "c", "description": "d", "voiceover": "v", "scenes": SC4[:1]})), [
    ("scenes != 4 -> expected four storyboard scenes", "r.ok === false && /four storyboard scenes/.test(r.error)", "r.error")]),
 ("seokit-err-emptykey", "seokit", oai(json.dumps({"title": "t", "hook_a": "", "hook_b": "b", "supporting_text": "s", "cta": "c", "description": "d", "voiceover": "v", "scenes": SC4})), [
    ("empty hook_a -> missing hook_a", "r.ok === false && /missing hook_a/.test(r.error)", "r.error")]),
 ("verify-ok", "verify", {"id": "job-123", "status": "planned", "url": None}, [
    ("accepted -> queued + renderId", "r.ok === true && r.status === 'queued' && r.renderId === 'job-123'", None),
    ("renderUrl null carried", "r.renderUrl === null", None),
    ("async warning", "/asynchronous/.test(r.warning)", None)]),
 ("verify-ok2", "verify", {"id": "job-456", "status": "rendering", "url": "https://cdn.creatomate/x.mp4"}, [
    ("renderStatus passthrough", "r.renderStatus === 'rendering'", None),
    ("renderUrl carried", "r.renderUrl === 'https://cdn.creatomate/x.mp4'", None)]),
 ("verify-noid", "verify", {"hint": "template not found"}, [
    ("no id -> upstream + hint details", "r.ok === false && r.errorCode === 'upstream' && /template not found/.test(r.details)", "JSON.stringify(r)")]),
 ("verify-error", "verify", {"error": "unauthorized"}, [
    ("v.error -> upstream", "r.ok === false && r.errorCode === 'upstream'", None)]),
 ("ready-succeeded", "ready", {"id": "r-1", "status": "succeeded", "url": "https://cdn/final.mp4", "snapshot_url": "https://cdn/snap.jpg"}, [
    ("succeeded -> ok + videoUrl + snapshotUrl", "r.ok === true && r.videoUrl === 'https://cdn/final.mp4' && r.snapshotUrl === 'https://cdn/snap.jpg'", None),
    ("ready message", "/Video ready/.test(r.message)", None)]),
 ("ready-failed", "ready", {"id": "r-2", "status": "failed", "errors": ["bad font"]}, [
    ("failed -> ok:false + errors carried", "r.ok === false && r.errors[0] === 'bad font'", None),
    ("failed -> videoUrl null", "r.videoUrl === null", None)]),
 ("ready-processing", "ready", {"id": "r-3", "status": "rendering"}, [
    ("processing -> ok:true no url + msg", "r.ok === true && r.videoUrl === null && /still processing/.test(r.message)", None)]),
 ("ready-error", "ready", {"error": "boom"}, [
    ("v.error -> upstream", "r.ok === false && r.errorCode === 'upstream'", None)]),
 ("norm-passthrough", "norm", {"error": "action must be draft, audit, render or status"}, [
    ("error passthrough + validation code", "r.ok === false && r.errorCode === 'validation' && /draft, audit, render or status/.test(r.error)", None)]),
 ("norm-unknown", "norm", {}, [
    ("missing error -> Unknown action", "r.error === 'Unknown action'", "r.error")]),
 ("preflight-ok", "preflight", {"audit": {"spoken_words": 80, "warnings": []}, "note": "deterministic"}, [
    ("audit passthrough -> audit_ready", "r.ok === true && r.status === 'audit_ready' && r.audit.spoken_words === 80 && r.note === 'deterministic'", None)]),
]

nodes = [node("t1", "When Executed by Another Workflow", "n8n-nodes-base.executeWorkflowTrigger", [-1400, 800], {}, 1, {"settings": {}})]
connections = {}
def add(src, dst, outIdx=0):
    c = connections.setdefault(src, {"main": []})
    while len(c["main"]) <= outIdx: c["main"].append([])
    c["main"][outIdx].append({"node": dst, "type": "main", "index": 0})

for i, (cname, unit, inp, checks) in enumerate(CASES):
    y = i * 160
    feed = "Feed " + cname
    unitn = "Unit " + cname
    asn = "Assert " + cname
    nodes.append(code("f%02d" % i, feed, [-1200, y], "return [{ json: %s }];" % json.dumps(inp, ensure_ascii=False)))
    nodes.append(code("u%02d" % i, unitn, [-950, y], UNITS[unit]))
    chk_lines = []
    for an, expr, got in checks:
        line = "checks.push({ name: %s, pass: !!(%s)" % (json.dumps(an, ensure_ascii=False), expr)
        if got: line += ", got: String(%s)" % got
        line += " });"
        chk_lines.append(line)
    ajs = ("const r = $input.first().json; const checks = [];\n" + "\n".join(chk_lines) +
           "\nconst passed = checks.filter(c => c.pass).length;" +
           "\nreturn [{ json: { suite: %s, passed, total: checks.length, checks } }];" % json.dumps(cname))
    nodes.append(code("a%02d" % i, asn, [-700, y], ajs))
    add("When Executed by Another Workflow", feed)
    add(feed, unitn); add(unitn, asn)

SUMMARY_JS = """
const suites = $input.all().map(i => i.json);
let passed = 0, total = 0;
for (const s of suites) { passed += s.passed; total += s.total; }
const failed = [];
for (const s of suites) for (const c of (s.checks || [])) if (!c.pass) failed.push(s.suite + ': ' + c.name + ' got=' + c.got);
return [{ json: { verdict: passed === total ? 'ALL_PASS' : 'FAIL', passed, total, failed, suites: suites.map(s => ({ suite: s.suite, passed: s.passed, total: s.total })) } }];
"""
nodes.append(code("sum", "Summary", [0, 1500], SUMMARY_JS))
for i, (cname, _, _, _) in enumerate(CASES):
    add("Assert " + cname, "Summary")

wf = {"id": "L2Test217160001", "name": "L2Test217160001", "nodes": nodes,
      "connections": connections, "settings": {}, "pinData": {}}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(wf, f, ensure_ascii=False, indent=1)
print("written", OUT, len(nodes), "nodes,", len(CASES), "cases,", sum(len(c[3]) for c in CASES), "asserts")