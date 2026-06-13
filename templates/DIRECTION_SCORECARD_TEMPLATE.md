# Direction Scorecard：[方向标题]

**方向编号**：[direction-slug]  
**项目编号**：[project-slug]  
**日期**：[YYYY-MM-DD]  
**risk_level**：[low / medium / high]  
**total_score**：[0-100]

## 评分表

评分口径：1 = 很弱或阻塞，2 = 脆弱，3 = 可做但缺口明显，4 = 适合低成本验证，5 = 证据直接且条件成熟。  
总分计算：`round(sum(scores) / 35 * 100)`。

| 维度 | 分数 1-5 | 理由 | 主要证据或缺口 |
|---|---:|---|---|
| Novelty | [1-5] | [说明] | [证据或缺口] |
| Feasibility | [1-5] | [说明] | [证据或缺口] |
| Data accessibility | [1-5] | [说明] | [证据或缺口] |
| Compute cost control | [1-5] | [说明] | [证据或缺口] |
| Evaluation clarity | [1-5] | [说明] | [证据或缺口] |
| Baseline reproducibility | [1-5] | [说明] | [证据或缺口] |
| Publication / project value | [1-5] | [说明] | [证据或缺口] |

## 继续理由

- [为什么仍值得做低成本检查。]
- [什么信号会让方向升格。]

## 停止理由

- [什么问题可能让方向不值得继续。]
- [什么证据一旦出现应停止或收窄。]

## recommended verdict

**结论**：[GO / STATIC_ONLY / NEEDS_MORE_EVIDENCE / NO_GO / USER_OVERRIDE]

**理由**：[说明 verdict 如何由分数、风险和证据缺口推出。]

## recommended next action

[下一步只写一个最小可执行动作，默认不使用训练或 GPU。]
