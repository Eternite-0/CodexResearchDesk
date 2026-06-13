# Pitfall Radar：VLM-based explainable open-set anomaly detection

**方向编号**：vlm-explainable-open-set-anomaly  
**项目编号**：vlm-open-set-anomaly-triage  
**日期**：2026-06-13  
**总体风险**：high

## 总览

**关键判断**：最大风险不是模型能否生成解释文本，而是这些解释是否新、是否忠实、是否能在开放集协议下被稳定评估。

## 风险雷达

| 类型 | risk description | warning signs | cheap pre-check | severity | mitigation |
|---|---|---|---|---|---|
| data pitfall | 公开数据缺少缺陷属性或解释标签，难以验证解释质量 | 只能报告 AUROC/AP，无法判断解释是否正确 | 审计 MVTec AD、VisA 等数据的标注粒度和可用 split | high | 将贡献收窄为协议设计或弱监督解释审计 |
| metric pitfall | 文本解释质量可能不可量化或只靠主观样例 | 论文展示少量好看的 case，没有忠实性指标 | 列出现有解释指标和可人工复核项 | high | 使用区域一致性、属性命中、反事实删除等可检查信号 |
| baseline pitfall | 选择弱 baseline 会夸大 VLM 贡献 | baseline 只含传统 CNN 或单一 CLIP 方法 | 建立近期 VLM/IAD baseline 清单 | high | 先做 baseline reproducibility 表，不跑训练 |
| novelty pitfall | “VLM + anomaly + explanation”可能已被密集覆盖 | 关键词检索出现多个近似标题和 claim | 2 年窗口的 closest-prior-work overlap check | high | 改写为更窄的开放集解释忠实性问题 |
| engineering pitfall | 多模态推理链、prompt 和后处理可能导致不可复现 | prompt 稍变结果大幅波动 | 对公开样例做 prompt 稳定性静态检查 | medium | 固定 prompt、输出格式和审计脚本 |
| evaluation pitfall | 开放集拆分可能和训练/验证泄漏混在一起 | unknown defect 类别在调参阶段被使用 | 审计 split 和调参协议 | high | 预注册 split，并保留未知类为最终评估 |
| paper/contribution pitfall | 贡献容易被认为只是应用 VLM | 方法贡献不清，指标只证明检测不证明解释 | 写出最小可发表 claim 并对照最近工作 | high | 把论文主张绑定到可验证解释忠实性 |

## 优先处理

| 优先级 | 先查什么 | 为什么先查 | 失败后的决策变化 |
|---:|---|---|---|
| 1 | 最近工作重合检查 | 决定 novelty 是否存在 | 若覆盖，改为 NO_GO 或大幅收窄 |
| 2 | 解释评估可行性 | 决定 claim 是否可证伪 | 若不可评估，回到 NEEDS_MORE_EVIDENCE |
| 3 | baseline 复现清单 | 决定后续实验成本 | 若强基线不可复现，只保留静态分析 |
