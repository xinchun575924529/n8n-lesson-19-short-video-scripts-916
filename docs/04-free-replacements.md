# 04 · 免费替身链（0 元跑通全流程）

## 替身总表

| 模板节点 | 付费原版 | 免费替身 | 本课验证 |
|----------|---------|---------|---------|
| Post to OpenAI | OpenAI gpt-4o-mini（按 token 计费） | **DeepSeek deepseek-chat** | ✅ C 关真跑 10/10 |
| Post to Creatomate | Creatomate $29/月起 | 本地 ffmpeg / Seedance | 方案 B/C 下文 |

## 1. LLM：OpenAI → DeepSeek（已实测）

DeepSeek 提供 OpenAI 兼容端点，**只改两处**（workflow-fixed.json 已改好）：

```
url:  https://api.openai.com/v1/chat/completions
   →  https://api.deepseek.com/v1/chat/completions

header: Authorization: Bearer YOUR_DEEPSEEK_API_KEY   # platform.deepseek.com 申请
model:  gpt-4o-mini → deepseek-chat                    # 在 Check Action 节点 requestBody 里
timeout: 30000 → 120000                                # DeepSeek 响应较慢，超时放宽
```

外加一个实测必须的补丁（见 docs/02 坑#5）：system prompt 追加词数硬约束。

成本参考：DeepSeek 按 token 计费但价格约为 OpenAI 的 1/10，单次 draft 调用约 ¥0.001 级；新账号有赠送额度。**真·0 元替代**：可换任何 OpenAI 兼容端点（本地 Ollama、硅基流动免费档等），改 url/model 即可。

## 2. 渲染：Creatomate → 本地方案

Creatomate 是托管渲染服务（$29/月起）。免费替代两条路：

### 方案 B：本地 ffmpeg 占位渲染（立即可用，0 元）
把 draft 产出的 storyboard（4 场景文案）渲染成"字幕卡视频"：

```bash
# 伪代码示意：4 张字幕卡 + 口播音频 → 9:16 mp4
ffmpeg -f lavfi -i color=c=0x0f1b2d:s=1080x1920:d=8 \
  -vf "drawtext=text='场景1文案':fontsize=64:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
  scene1.mp4
# 4 段 concat + 音频合成 → final.mp4
```
n8n 侧：把 `Post to Creatomate` 换成 `Execute Command` 节点跑本地脚本，返回 `{id, status:'succeeded', url}`——status 路由逻辑不用动。

### 方案 C：AI 生视频（Seedance / 可灵等，进阶）
draft 的 `scenes[].visual_direction` 字段本来就是给生成模型用的镜头描述：
- 4 个场景 → 4 次图生视频/文生视频调用 → 拼接
- 渲染时间几分钟，正好匹配模板"render 拿 id → status 轮询"的异步设计
- 注意口型同步（lip-sync）需额外环节，纯口播片建议用方案 B 字幕卡

## 3. 部署形态建议

| 场景 | 建议 |
|------|------|
| 学习/POC | 本地 n8n + DeepSeek + ffmpeg 方案 B，0 元全链 |
| 小团队生产 | n8n 云/服务器 + DeepSeek + Creatomate（省心）或方案 C |
| 卖 API 服务 | 加鉴权/限流/余额巡检（见 docs/05）再上架 |