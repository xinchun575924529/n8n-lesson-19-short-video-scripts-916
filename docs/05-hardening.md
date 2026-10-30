# 05 · 上线加固清单

模板本身护栏已属上乘，但要真当 API 产品卖，还差这几刀：

## 1. 鉴权（必做）
模板 webhook 裸奔，任何人知道 URL 就能刷你的 LLM 额度。
- 最简：webhook 节点开 Header Auth（n8n 内置），调用方带 `Authorization: Bearer <随机长串>`
- 进阶：前置一个 Code 节点校验签名/API key 池

## 2. 限流与余额巡检（必做）
- LLM key 余额：`GET https://api.deepseek.com/user/balance`，定时巡检 + 阈值告警（研发期实锤：余额 -0.40 元时全部 draft 静默 502）
- 调用方限流：n8n 层可用 Redis/内存计数，或直接上 Cloudflare/网关层限流

## 3. LLM 返回截断检测（建议）
- 检查 `choices[0].finish_reason`：`length` = 被截断，应 retry 或报错，别硬解析
- 修复版对 DeepSeek 官方端点实测无此问题；换免费端点必须加

## 4. 重试策略（建议）
- LLM http 节点：`retryOnFail: true, maxTries: 3, waitBetweenTries: 5000`（节点级 settings，写在 parameters 里无效——n8n 2.x 坑）
- 渲染提交节点同理；status 查询节点不需要（本来就是轮询语义）

## 5. 超时（已内置）
- DeepSeek 响应比 OpenAI 慢，timeout 建议 120000ms（修复版已调）

## 6. 观测（建议）
- draft 链落库：topic/平台/词数/告警 → 后续分析"什么主题容易被告警"
- 渲染成功率、LLM 502 率 → 飞书/邮件告警

## 7. 版权与合规（法务向）
- render 双闸门（approved + rights_confirmed）就是为此设计，**生产上别绕过**
- audit 的人工检查清单（素材授权/音乐版权/平台条款）建议做成内部 SOP 文档，不只靠 API 返回

## 8. 批量调用注意
模板 Code 是 `$input.first()` 单条模式，批量 draft 请调用方逐条发请求，不要塞数组。