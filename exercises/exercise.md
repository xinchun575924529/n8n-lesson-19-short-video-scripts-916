# 练习（4 题，由浅入深）

## 练习 1 · 跑通 draft（入门）
导入 `workflow-fixed.json`，填入你的 DeepSeek key，激活工作流，用 curl 调 draft：

```bash
curl -X POST http://localhost:5678/webhook/<你的path> \
  -H "Content-Type: application/json" \
  -d '{"action":"draft","topic":"为什么手冲咖啡比速溶好喝","platform":"tiktok","audience":"咖啡入门玩家","tone":"轻松幽默"}'
```

**验收**：返回 200 + `draft.scenes` 恰好 4 个 + `copy_preflight.voiceover_length_warning=false`。
**观察**：如果词数被告警，重跑几次体会 LLM 波动性（docs/02 坑#5）。

## 练习 2 · 玩转 audit 护栏（理解校验）
构造 4 个 audit 请求，各触发一类告警：
1. 标题超过 95 字符
2. 口播稿 200 词
3. hook 和 title 一模一样
4. 文案里写 "100% guaranteed results"

**验收**：4 个请求的 `audit.warnings` 各含对应告警，且 `passed_basic_copy_checks=false`。
**思考**：为什么这些检查用确定性代码做而不是让 LLM 做？

## 练习 3 · 双闸门类型测试（理解契约）
调 render 三次：
1. `"approved": true, "rights_confirmed": true`（布尔）
2. `"approved": "true", "rights_confirmed": "true"`（字符串）
3. 缺一个字段

**验收**：① 走到渲染提交（mock 下 queued）②③ 都是 400。
**思考**：API 契约里"严格类型"和"宽容解析"的取舍。

## 练习 4 · 免费渲染替身落地（进阶，综合）
按 docs/04 方案 B，把 `Post to Creatomate` 换成 Execute Command 跑本地 ffmpeg：
- 输入：draft 产出的 4 场景 `on_screen_text`
- 输出：4 张字幕卡合成的 9:16 mp4，返回 `{id, status:'succeeded', url}`
- 然后调 status 应能拿到 videoUrl

**验收**：从 draft 到 status 拿成片，全程 0 元，不碰 Creatomate。
**加分**：把渲染改成异步（立即返回 id，后台渲染），体验模板的无状态设计。