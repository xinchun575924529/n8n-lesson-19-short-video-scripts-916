# 01 · 架构拆解（20 节点 / 5 路由）

## 总览图

```
POST /webhook
   │
   ▼
Check Action and Budget Validity (code)  ← 入参白名单校验 + 组 LLM prompt
   │
   ▼
Route by Video Task (switch, 5 出口)
   ├─ draft ──► Post to OpenAI/DeepSeek (http) ──► Build SEO Kit from Script (code) ──► Respond 200
   ├─ render ─► Post to Creatomate (http) ──► Verify Render Job Submission (code) ──► Respond 200/502
   ├─ status ─► Fetch Creatomate Render Status (http) ──► Check Video Readiness (code) ──► Respond
   ├─ audit ──► Execute Preflight Script Check (code) ──► Respond 200
   └─ Other ──► Handle and Normalize Input Errors (code) ──► Respond 400
```

## 逐节点职能

### 入口层
1. **When Video Request Received**（webhook）：POST 入口，全模板唯一触发器。
2. **Check Action and Budget Validity**（code）：第一个 Code 节点，干三件事——
   - action 白名单（draft/render/status/audit），非法走 Other
   - draft 分支：topic 5–400 字符、language/audience/tone 非空、**platform 白名单但非法值静默降级 youtube**
   - draft 分支：现组 OpenAI 兼容 `requestBody`（system prompt + user prompt，要求严格 JSON 输出）

### draft 路由（AI 核心）
3. **Post to OpenAI for Hook Variations**（http）：`POST /v1/chat/completions`，body 直接用上游组的 `requestBody`；`onError=continueRegularOutput`（错误不中断，交下游归一化）。
4. **Build SEO Kit from Script**（code）：全模板最重的节点——
   - 解析 LLM 返回（容错剥离 markdown 围栏）
   - schema 强校验：7 个非空字符串键 + hashtags/seo_keywords/scenes 数组 + **恰好 4 场景**且每场景 3 字段
   - 截断清洗：title≤95、hashtag 自动补 `#`、数量收敛 3–8
   - 组装三平台发布 kit（youtube title / tiktok caption / instagram caption）
   - **copy_preflight**：口播词数统计 + `voiceover_length_warning` 护栏
   - 上游错误归一化：`AI request failed or returned truncated content` → 502

### render 路由（人工闸门）
5. **Post to Creatomate for Rendering**（http）：提交 9:16 渲染。
6. **Verify Render Job Submission**（code）：**双闸门严格 `===` 校验**——`approved===true && rights_confirmed===true` 必须是布尔，字符串 `"true"` 被拦（400）；渲染 API 故障 → 502。

### status 路由（异步轮询）
7. **Fetch Creatomate Render Status**（http）：按 render_id 查状态。
8. **Check Video Readiness**（code）：`render_id` 必须过 UUID 正则；succeeded → 返回 videoUrl；failed → 502；处理中 → 返回进度。

### audit 路由（纯本地护栏）
9. **Execute Preflight Script Check**（code）：零外部调用的确定性预检——词数（65–105）、标题≤95、绝对化用语正则（**含阿拉伯语** `اغتنم الفرصة مضمونة`）、hook=title 撞车检测；附人工检查清单和免责声明。

### 错误归一化
10. **Handle and Normalize Input Errors**（code）：所有校验失败/未知 action 统一 400 格式 `{ok:false, action:'invalid', errorCode:'validation', error}`。

## 设计范式（背下来）

- **单入口多动作**：一个 webhook + switch 路由，比一堆 webhook 好维护
- **校验前置**：第一个节点就拦垃圾输入，LLM 只见到干净 prompt
- **错误分级**：调用方错 → 400；上游（AI/渲染）错 → 502；语义清晰
- **无状态异步**：render 拿 id、status 查 id，工作流本身不挂轮询
- **护栏多层**：入参校验 → LLM 输出 schema 校验 → audit 预检 → 人工双闸门，层层递进