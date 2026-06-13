# Direction Brief：VLM-based explainable open-set anomaly detection

**方向编号**：vlm-explainable-open-set-anomaly  
**项目编号**：vlm-open-set-anomaly-triage  
**日期**：2026-06-13  
**初步结论**：STATIC_ONLY  
**置信度**：medium

## 一句话方向

用视觉-语言模型为开放集异常检测提供可审查的缺陷解释，同时保持检测协议对未知缺陷类别有效。

## 核心 research claim

**主张**：VLM 的语义先验可以帮助开放集异常检测输出更可解释的缺陷描述，并且这种解释能被独立指标或人工审查验证，而不是只作为检测分数的附属文本。

**必要条件**：公开数据集能构造合理的开放集拆分；解释质量有可复核指标；VLM 方法相对强基线有清晰差异；不需要先训练新大模型才能看到信号。

**可能推翻它的观察**：最近工作已经覆盖同一 claim；解释文本与真实缺陷区域或类别无稳定对应；强 CLIP/VLM 基线在相同协议下已经给出同等解释能力。

## 为什么值得做

- 工业异常检测需要让工程人员理解缺陷原因，单一 anomaly score 难以支持排查。
- 开放集设置贴近真实产线中新缺陷类别不断出现的场景。
- 如果成立，最小贡献可以是一个可复核的解释忠实性评估协议，而不一定是新模型。

## 需要的已有证据

| 证据项 | 当前状态 | 对决策的影响 |
|---|---|---|
| 2024-2026 年 VLM/CLIP 工业异常检测相关工作 | 待核验 | 直接影响 novelty |
| MVTec AD、VisA 等公开数据能否构造开放集解释评估 | 部分可查 | 影响 feasibility |
| 解释文本是否能和缺陷区域、属性或人工标签对应 | 缺失 | 影响核心 claim |

## novelty 问题

- VLM 用于工业异常检测已经是拥挤方向，必须确认“开放集 + 可解释 + 忠实性评估”是否只是已有工作的重新表述。
- 新意不应落在“用了 VLM 生成解释”本身，而应落在可检验的解释可靠性、未知缺陷处理或评估协议上。
- 优先查新关键词：open-set anomaly detection、industrial anomaly explanation、CLIP anomaly detection、VLM defect reasoning、explainable anomaly detection。

## feasibility 问题

- 数据集是否有足够缺陷属性或区域标注支持解释评估仍不确定。
- baseline 需要包括强 CLIP/VLM 异常检测方法，不能只和传统视觉模型比较。
- 先做静态协议审计和公开输出样例分析，避免直接进入训练。

## Top 3 risks

| 风险 | 严重性 | 为什么重要 |
|---|---|---|
| novelty 被近期 VLM 异常检测工作覆盖 | high | 如果核心 claim 已被覆盖，继续实验价值很低 |
| 解释指标不可验证 | high | 没有忠实性指标时，解释可能只是漂亮文本 |
| 开放集拆分不稳定 | medium | 协议不稳会导致结果不可比较 |

## lowest-cost next check

| 项目 | 内容 |
|---|---|
| 检查方式 | 最近工作重合检查和公开 benchmark protocol 审计 |
| 预期成本 | 6-8 小时，0 GPU |
| 通过条件 | 没有近期工作完整覆盖核心 claim，且至少一个公开数据集能定义可复核解释协议 |
| 失败条件 | 已有工作覆盖同一 claim，或解释评估只能依赖主观文本好坏 |

## preliminary verdict

**结论**：STATIC_ONLY

**理由**：方向有现实价值，但 novelty 和解释忠实性是阻塞风险。下一步应只做查新、协议审计和非训练探针，不应启动 GPU 训练或大规模标注。
