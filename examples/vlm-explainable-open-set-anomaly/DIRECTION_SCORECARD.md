# Direction Scorecard：VLM-based explainable open-set anomaly detection

**方向编号**：vlm-explainable-open-set-anomaly  
**项目编号**：vlm-open-set-anomaly-triage  
**日期**：2026-06-13  
**risk_level**：high  
**total_score**：57

## 评分表

评分口径：1 = 很弱或阻塞，2 = 脆弱，3 = 可做但缺口明显，4 = 适合低成本验证，5 = 证据直接且条件成熟。  
总分计算：`round(20 / 35 * 100) = 57`。

| 维度 | 分数 1-5 | 理由 | 主要证据或缺口 |
|---|---:|---|---|
| Novelty | 2 | VLM 异常检测方向拥挤，核心差异尚未证明 | 需要最近工作重合检查 |
| Feasibility | 3 | 可先用公开数据和公开模型做静态审计 | 解释标注不足 |
| Data accessibility | 3 | 常见工业异常数据可得，但解释标签有限 | 需要 split 和标签审计 |
| Compute cost control | 4 | 初期可 0 GPU 完成查新、协议审计和非训练探针 | 训练阶段暂不允许 |
| Evaluation clarity | 2 | 检测指标清楚，解释忠实性指标不清楚 | 需要定义可复核指标 |
| Baseline reproducibility | 3 | 公开 baseline 可能存在，但近期 VLM baseline 成本未知 | 需要复现清单 |
| Publication / project value | 3 | 工业解释价值明确，但贡献边界尚窄 | 需要证明不只是 VLM 应用 |

## 继续理由

- 真实场景需要开放集缺陷解释，问题不是伪需求。
- 初期验证可以保持低成本，不需要立刻训练。
- 如果能定义忠实性评估协议，贡献可能从“新模型”转为“可审查评估”。

## 停止理由

- 最近工作可能已经覆盖核心 claim。
- 没有可靠解释指标时，方向容易退化成样例展示。
- 强 VLM baseline 如果已经足够，新增方法空间很小。

## recommended verdict

**结论**：STATIC_ONLY

**理由**：总分 57/100 且总体风险 high，说明方向有价值但证据不足。允许查新、协议审计和非训练探针；不允许训练或 GPU pilot。

## recommended next action

先做 6-8 小时最近工作重合检查，并输出 closest-prior-work 表。
