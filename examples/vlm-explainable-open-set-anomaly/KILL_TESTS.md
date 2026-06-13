# Kill Tests：VLM-based explainable open-set anomaly detection

**方向编号**：vlm-explainable-open-set-anomaly  
**项目编号**：vlm-open-set-anomaly-triage  
**日期**：2026-06-13  
**目标 verdict**：STATIC_ONLY

## 设计原则

这些测试只用于决定是否继续补证或收窄方向，不证明方法有效。默认不启动训练、GPU pilot 或长任务。

## Kill Tests

| test name | hypothesis | expected cost | pass condition | fail condition | decision change if failed |
|---|---|---|---|---|---|
| 最近工作重合检查 | 核心 claim 尚未被近期 VLM 工业异常检测工作完整覆盖 | 4-6 小时，0 GPU | closest-prior-work 表中没有工作同时覆盖开放集、解释忠实性和同类评估协议 | 至少 2-3 篇近期工作已经完整覆盖该 claim | 改为 NO_GO，或仅保留更窄的评估协议方向 |
| 解释忠实性可评估性检查 | 公开数据能支持解释是否对齐缺陷区域或属性的基本审计 | 2-3 小时，0 GPU | 至少一个数据集有可复核区域、类别或属性信号 | 只能主观阅读文本，无法形成可重复指标 | 改为 NEEDS_MORE_EVIDENCE |
| baseline 复现清单检查 | 强 CLIP/VLM baseline 的评估协议可复现或可公平引用 | 3-4 小时，0 GPU | 找到至少 2 个可复核 baseline 和明确协议 | baseline 缺代码、缺 split 或协议不可比 | 维持 STATIC_ONLY，禁止进入实验 |
| 开放集 split 泄漏检查 | unknown defect 类别可以在不泄漏调参的情况下保留到最终评估 | 2 小时，0 GPU | split 规则可预注册，未知类不进入调参 | unknown 类别必须参与 prompt 或阈值选择 | 收窄为 closed-set 解释审计，或停止 |

## 判定规则

- **立即停止条件**：最近工作已覆盖核心 claim，且本方向没有更窄、可检验的差异。
- **收窄条件**：解释指标不可量化，但仍可做数据协议或 baseline 审计。
- **升级条件**：完成查新、解释指标和 baseline 清单后，再写 Decision Memo 并通过 gate。
