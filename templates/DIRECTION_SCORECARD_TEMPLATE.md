# Direction Scorecard：[方向标题]

**方向编号**：[direction-slug]  
**项目编号**：[project-slug]  
**日期**：[YYYY-MM-DD]  
**risk_level**：[low / medium / high]  
**total_score**：[0-100]

## 评分表

评分口径：1 = 很弱或阻塞，2 = 脆弱，3 = 可做但缺口明显，4 = 适合低成本验证，5 = 证据直接且条件成熟。  
总分计算：`round(sum(scores) / 35 * 100)`。  
外部信号和论文到代码库追踪只作为风险证据和优先级提示，不直接进入总分，避免被热度或仓库表象绑架。

| 维度 | 分数 1-5 | 理由 | 主要证据或缺口 |
|---|---:|---|---|
| Novelty | [1-5] | [说明] | [证据或缺口] |
| Feasibility | [1-5] | [说明] | [证据或缺口] |
| Data accessibility | [1-5] | [说明] | [证据或缺口] |
| Compute cost control | [1-5] | [说明] | [证据或缺口] |
| Evaluation clarity | [1-5] | [说明] | [证据或缺口] |
| Baseline reproducibility | [1-5] | [说明] | [证据或缺口] |
| Publication / project value | [1-5] | [说明] | [证据或缺口] |

## 外部信号与坑位证据

| 项目 | 判断 |
|---|---|
| external_signal_score | [0-100；来自 `projects/<project-slug>/signals/<direction-slug>/external_signals.json`，没有则写“未使用”] |
| hype_risk | [low / medium / high；热度高但缺 benchmark/trace 时提高] |
| 工程健康 | [GitHub 维护、license、CI、release、issue 等信号] |
| 社区与论文热度 | [alphaXiv / HF Papers / HN / 手工 X/Reddit 信号] |
| 企业或机构采用 | [Microsoft/HF/企业采用/产品集成/benchmark 组织等信号] |
| 坑位假设 | [外部信号暴露的风险，例如无指标、赛道拥挤、工程不可复现、只有 hype] |
| A+B 检查 | [说明为什么这个 idea 不是简单拼接两个流行方向；如果不能说明，降级为补证或停止理由] |

## 论文到代码库追踪

| 项目 | 判断 |
|---|---|
| paper_code_trace_score | [0-100；来自 `projects/<project-slug>/signals/<direction-slug>/paper_code.json`，没有则写“未使用”] |
| code_availability_risk | [low / medium / high] |
| 论文到仓库关系 | [官方链接 / Papers with Code / arXiv 页面 / README 命中 arXiv ID 或标题 / 未确认] |
| 静态可审计性 | [是否有 install、data、checkpoint、config、evaluation、result table 信号] |
| 复用边界 | [license、维护状态、是否 archived、是否 code coming soon、是否 unofficial] |
| 对方向评分的影响 | [说明它如何影响 Feasibility、Evaluation clarity、Baseline reproducibility，而不是把仓库热度直接当分数] |

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
