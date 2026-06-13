# Subagent Task：[task title]

**项目编号**：[project-slug]  
**运行编号**：[run-slug]  
**子任务编号**：[packet-slug]  
**任务类型**：[Seed Scan / Paper-Code Trace / External Signal / Pitfall Review / Novelty Probe / Kill Test Design]  

## 单一问题

[这个子代理只回答一个问题。不要扩展成完整调研。]

## 输入材料

| 类型 | 内容 | 备注 |
|---|---|---|
| paper | [title / arXiv / DOI] | [可选] |
| repo | [owner/repo / URL] | [可选] |
| query | [关键词] | [可选] |
| local path | [项目内路径] | [可选] |

## 允许来源

- 本地项目文件和已有 ledger。
- 指定论文、仓库和公开元数据。
- 外部检索只用于回答本任务问题。

## 上下文预算

- 最终输出目标：400-800 中文字，加紧凑表格。
- 不粘贴论文全文、README 全文、源码长段、网页长段。
- 引用链接、路径、指标和极短证据片段即可。

## 停止条件

- 已经能支持 `promote / static_precheck / narrow / drop` 中一个动作。
- 或关键来源不可得，且缺口本身足以进入主 Agent 的风险台账。

## 禁止事项

- 不生成 Decision Memo。
- 不设计训练实验或 GPU 任务。
- 不全量 clone 或读取代码库。
- 不把多个问题合并成一个 packet。
- 不替主 Agent 做最终候选排序。

## 必须输出

写入：

```text
projects/<project-slug>/evidence-packets/<run-slug>/<packet-slug>.md
```

使用 `templates/EVIDENCE_PACKET_TEMPLATE.md`，并在最后给出：

- 一句话结论。
- 建议动作：`promote / static_precheck / narrow / drop`。
- 下一步最低成本检查。
