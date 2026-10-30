# 02 · 坑与修复（实锤）

## A. 模板自带观察点（原作者行为，教学讨论用）

### 1. platform 非法值静默降级 youtube ⭐讨论点
`Check Action and Budget Validity` 里：`['youtube','tiktok','instagram'].includes(platform) ? platform : 'youtube'`。
传 `platform:"linkedin"` 不报错，静默按 youtube 处理。
- **优点**：调用方永不被打断
- **缺点**：调用方以为发了 linkedin kit，实际拿到 youtube
- **讨论**：API 设计里"静默降级 vs 显式报错"怎么选？（参考答案：写进响应体 `platform` 字段回显，让调用方可自查——模板确实回显了，算半个好设计）

### 2. 双闸门严格 `===` 布尔校验
`Verify Render Job Submission`：`approved===true && rights_confirmed===true`。
JSON 里传 `"approved":"true"`（字符串）→ 400 拦下。
- **教学点**：涉及钱/版权的闸门，严格类型是优点不是刁难；调用方文档要写清布尔类型。

### 3. audit 是确定性预检，不是事实核查
模板作者在 audit 响应里明确写了免责：`note: This is a deterministic preflight check...`。
- **教学点**：LLM 应用要分清"机器能保证的"（词数/长度/正则）和"机器不能保证的"（事实/版权），并在 API 响应里诚实标注。

### 4. 无状态 render/status 设计
渲染是异步的（几十秒~几分钟），模板选择：render 返回 render_id，调用方自己轮询 status。
- **教学点**：长任务 API 的标准形态；对比"工作流内挂 Wait 循环"的坏处（占用执行、超时风险、重试难）。

## B. 实锤坑（我们研发中真实踩到，修复版已修）

### 5. LLM 词数漂移：prompt 约束不够硬 ⭐最有价值
system prompt 写了"65–105 spoken words"，DeepSeek 首跑交出 **141 词**（超标 34%）。
- **结果**：被 `copy_preflight.voiceover_length_warning` 正确告警——**证明护栏不是摆设**
- **修复**（workflow-fixed.json 已内置）：system prompt 末尾追加硬性约束——
  `STRICT LENGTH CONTROL: the voiceover field MUST be 65-100 English words. Count the words before answering; if outside range, rewrite until it fits.`
- **效果**：重跑 80 词，稳定通过。
- **教训**：LLM 的"软要求"会被无视，关键数值约束要写成"hard requirement + 动作指令（count/rewrite）"；同时护栏层必须独立存在，不能指望 prompt。

### 6. 上游故障要归一化成 502，别裸奔
LLM/渲染 API 挂了，模板靠 `onError=continueRegularOutput` + 下游 Code 归一化 → `{errorCode:'upstream', ...}` 502。
- **测试实证**（B-E4 场景）：模拟 OpenAI 故障，调用方收到干净 502，不是 n8n 错误堆栈。
- **教训**：`onError`/`retryOnFail` 必须配在**节点级**，写在 parameters 里无效（n8n 2.x）。

### 7. 模板 Code 用 `$input.first()`，多 item 会静默漏处理
模板所有 Code 节点都是 `$input.first().json`（runOnceForAllItems 模式）。
- **坑**：如果你给它喂多条 item（比如批量 draft），只处理第一条，其余静默丢弃。
- **教训**：单元测试每个 case 必须独立分支/独立执行；生产上批量调用要逐条发请求。

## C. 环境/基建坑（研发环境实锤，学员可能遇到）

### 8. LLM 返回截断要检测 finish_reason
免费/低配 LLM 端点常有 max_tokens 上限，返回截断 JSON → 解析失败。
- **修复版措施**：DeepSeek 官方端点无此问题（余额充足时）；若换其他免费端点，检查 `choices[0].finish_reason==='length'` 并 retry。
- **实锤**：研发期探测 Pollinations 免费端点（1500 token 上限 + 推理模型烧 token），正文必截断，不可用，弃。

### 9. 余额耗尽是静默杀手
DeepSeek key 余额 -0.40 元时，draft 链报 `AI request failed or returned truncated content`（402 被归一化）。
- **建议**：生产环境加余额巡检（`GET /user/balance`），低于阈值告警——比用户投诉才发现强。