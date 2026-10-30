# Lesson 19: 短视频脚本生成 + 9:16 渲染 API 工作流

> 基于 n8n 官方模板 [#21716](https://n8n.io/workflows/21716/)（Generate short-form video scripts and render 9:16 clips with OpenAI and Creatomate）

## 是什么?

一个 **webhook API 工作流**，一个入口四个动作，把"AI 写短视频脚本 → 人工审批 → 提交渲染 → 轮询取片"做成标准 HTTP 接口：

1. `action=draft`：给主题，AI 产出标题/双 hook/4 场景 storyboard/口播稿/hashtag/三平台发布 kit
2. `action=audit`：粘贴文案，本地确定性预检（词数、标题长度、绝对化用语、hook=title 撞车）
3. `action=render`：双人工闸门（approved + rights_confirmed）后提交 9:16 渲染
4. `action=status`：凭 render_id 查渲染状态，成功返回成片 URL

**教学卖点：这是"API 工作流的正确姿势"课**——入参白名单校验、双闸门人工审批、400/502 错误分级、schema 严格校验、无状态异步轮询，护栏设计完整。

## 课程包内容

| 文件 | 说明 |
|------|------|
| `workflow.json` | n8n 官方模板原版（OpenAI + Creatomate，付费路线） |
| `workflow-fixed.json` | **中文修复版**：DeepSeek 替换 OpenAI（实测真跑过）、prompt 加词数硬约束 |
| `docs/00-overview.md` | 课程总览与适用人群 |
| `docs/01-architecture.md` | 逐节点架构拆解（20 节点 / 5 路由） |
| `docs/02-pitfalls.md` | 模板观察 + 实锤坑（含修复方案） |
| `docs/03-l2-verification.md` | L2 三关验证报告（**A 81/81 + B 28/28 + C 10/10 = 119 断言全绿**） |
| `docs/04-free-replacements.md` | 0 元替身链：DeepSeek / ffmpeg·Seedance 渲染替代 |
| `docs/05-hardening.md` | 上线加固清单（鉴权/限流/重试/截断检测） |
| `exercises/exercise.md` | 4 个动手练习 |
| `script/short-video.md` | 课程宣发口播脚本 |
| `scripts/` | L2 三关测试生成器与运行器（可复跑） |

## 模板 4 大观察（实锤）

1. **LLM 词数漂移**：prompt 写"65–105 词"DeepSeek 首跑给了 141 词——护栏（audit 词数告警）正确兜底；修复版在 system prompt 追加硬性词数约束后稳定 80 词。**护栏不是摆设，是 LLM 工作流的必需品。**
2. **platform 非法值静默降级 youtube**（不报错）——"静默降级 vs 显式报错"的经典讨论案例。
3. **render 双闸门严格 `===` 校验**：字符串 `"true"` 会被拦下，必须布尔 `true`——API 契约严谨性教学点。
4. **无状态设计**：render/status 靠 `render_id` 串联，调用方自管轮询——异步 API 设计范式。

## 免费替身链

| 模板节点 | 付费原版 | 免费替身（本课实测） |
|----------|---------|---------------------|
| OpenAI gpt-4o-mini | 按 token 计费 | **DeepSeek deepseek-chat**（C 关真跑 10/10） |
| Creatomate 渲染 | $29/月起 | 本地 ffmpeg 占位渲染 / Seedance 生视频（见 docs/04） |

## 验证结论

L2 三关全绿：A 单元级 81/81（42 case）、B mock 全链 28/28（9 场景）、C 免费真跑 10/10（DeepSeek 真实产出蜜蜂主题脚本 + mock 渲染链）。详见 `docs/03-l2-verification.md`。