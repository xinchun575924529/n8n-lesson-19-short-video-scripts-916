# 03 · L2 三关验证报告

日期：2026-10-29/30 ｜ 结论：**A 81/81 + B 28/28 + C 10/10 = 119 断言全绿**

## A 关 · 单元级（81/81）
- 工作流 `L2Test217160001`（128 节点，42 case）；生成器 `scripts/build-l2-test-21716.py`；结果 `scripts/l2a-21716-result.json`
- 6 个 Code 节点**逐字忠实移植**；覆盖四 action 全部正例/失败分支
- 明细：draft 默认值与失败分支 9 项、平台白名单与静默降级、audit 五类告警（标题>95 / 词数越界 / hook=title / 英文+阿拉伯语绝对化正则）、render 双闸门严格 `===`（字符串 `'true'` 被拦）、status UUID 正则、seokit 截断与 hashtag 清洗、4 场景强校验、上游 5 类错误归一化
- 技术记录：①模板 Code 用 `$input.first()`，多 case 测试须每 case 独立分支；②多分支汇聚 Summary 会多次执行，按 suite 名合并取全量

## B 关 · mock 全链（28/28，9 场景）
- 9 个场景工作流 `L2Mock21716{S1-S5,E1-E4}01`；生成器 `scripts/build-l2-mock-21716.py`
- 保留模板全结构（webhook→校验→Switch 5 出口含 fallback Other），外部依赖全 mock；respondToWebhook 替换为 Capture（复刻 responseCode 表达式 200/400/502）
- 场景：
  - S1 draft 全链 200 + 三平台 kit
  - S2 render 双闸门通过 → queued
  - S3 status succeeded → videoUrl
  - S4 status failed → 502
  - S5 audit → preflight 报告
  - E1 未知 action → Other → 400
  - E2 topic 过短 → 400
  - E3 未审批 render（字符串 true）→ 400
  - E4 OpenAI 故障 → 502

## C 关 · 免费真跑（10/10）
- 工作流 `L2Cstm21716001`（22 节点）；生成器 `scripts/build-l2c-21716.py`
- **draft 链 DeepSeek 真调**：真实产出"蜜蜂授粉"主题脚本——标题 ≤95 字符、双 hook 互异、恰好 4 场景 storyboard、80 词口播（护栏无告警）、3–8 个带 `#` hashtag、三平台发布 kit、主题词嵌入
- render/status 链走 mock Creatomate（付费项，按定案 mock）：queued → renderId 校验 → succeeded → videoUrl
- **事故与恢复**：DeepSeek key 余额 -0.40 元 402 → 充值后恢复；期间探测 Pollinations 免费替身（gpt-oss-20b 推理模型 + 1500 token 上限 + 30s/IP 限流）必截断，不可用，弃
- **LLM 波动性实证**：首跑 voiceover 141 词被 preflight 正确告警（护栏工作正常的活证据），prompt 加硬约束后重跑 80 词通过

## 复跑方式

```bash
# A 关
python scripts/build-l2-test-21716.py && python scripts/run-l2a-21716.py
# B 关
python scripts/build-l2-mock-21716.py && python scripts/run-l2-mock-21716.py
# C 关（需 state/deepseek-key.json 有效余额）
python scripts/build-l2c-21716.py && python scripts/run-l2c-21716.py
```