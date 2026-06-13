# Kill Tests：[方向标题]

**方向编号**：[direction-slug]  
**项目编号**：[project-slug]  
**日期**：[YYYY-MM-DD]  
**目标 verdict**：[STATIC_ONLY / NEEDS_MORE_EVIDENCE / NO_GO / GO]

## 设计原则

至少 3 个低成本 kill tests；至少 1 个测试必须能快速否定该方向或迫使方向大幅收窄。默认不启动训练、GPU pilot 或长任务。

## Kill Tests

| test name | hypothesis | expected cost | pass condition | fail condition | decision change if failed |
|---|---|---|---|---|---|
| [测试 1，快速否定测试] | [待检验假设] | [小时/API/GPU，默认 0 GPU] | [通过条件] | [失败条件] | [停止 / 收窄 / 回到查新] |
| [测试 2] | [待检验假设] | [小时/API/GPU，默认 0 GPU] | [通过条件] | [失败条件] | [停止 / 收窄 / 回到查新] |
| [测试 3] | [待检验假设] | [小时/API/GPU，默认 0 GPU] | [通过条件] | [失败条件] | [停止 / 收窄 / 回到查新] |

## 判定规则

- **立即停止条件**：[例如核心 claim 已被近期工作覆盖，或关键数据不可得。]
- **收窄条件**：[例如只能保留一个更小、更可测的 claim。]
- **升级条件**：[例如通过所有静态检查后，才进入 Decision Memo 和 gate。]
