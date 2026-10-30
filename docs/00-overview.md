# 00 · 课程总览

## 一句话

把"AI 写短视频脚本 → 人工审 → 渲染 9:16 → 取成片"做成**四个 HTTP 接口**的生产级 webhook 工作流。

## 为什么学这个

市面上大多数 n8n 教程教的是"流程自动化"（A 触发 B）。这个模板教的是另一种更值钱的形态：**把工作流包装成 API 产品**——

- 前端/App/机器人 只管 `POST /webhook/xxx {"action":"draft","topic":"..."}`
- 工作流内部做校验、调 AI、人工闸门、错误分级
- 调用方拿到的是结构化 JSON，不是聊天记录

学完你能把任何"AI 生成+人工审核"类需求包装成干净的后端接口。

## 模板名片

| 项 | 值 |
|---|---|
| 模板编号 | n8n.io/workflows/21716 |
| 原名 | Generate short-form video scripts and render 9:16 clips with OpenAI and Creatomate |
| 节点数 | 20（不含 7 张便签） |
| 核心节点 | webhook × 1、code × 6、switch × 1、httpRequest × 3、respondToWebhook × 5 |
| 外部依赖 | OpenAI（→免费替身 DeepSeek）、Creatomate（→ffmpeg/Seedance） |

## 四个 action 速览

| action | 干什么 | 外部调用 |
|--------|--------|---------|
| `draft` | 主题 → 完整脚本包（标题/双 hook/4 场景/口播/hashtag/三平台 kit） | LLM |
| `audit` | 文案 → 确定性预检报告（词数/标题/绝对化用语/撞车） | 无（纯本地） |
| `render` | 双闸门通过 → 提交 9:16 渲染任务 | 渲染 API |
| `status` | render_id → 渲染进度/成片 URL | 渲染 API |

## 适合谁

- 想给短视频团队/MCN 做脚本生产后台的人
- 想把 n8n 工作流当 API 卖的人
- 正在学"LLM 工作流护栏设计"的人（这模板护栏是教科书级）