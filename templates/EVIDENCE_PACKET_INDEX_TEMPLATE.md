# Evidence Packet Index：[run-slug]

**项目编号**：[project-slug]  
**运行编号**：[run-slug]  
**生成时间**：[YYYY-MM-DD HH:mm]  

## Packet 总表

| packet | 子任务 | 路径 | 一句话结论 | 建议动作 | 是否需要打开原始来源 |
|---|---|---|---|---|---|
| [packet-slug] | [Seed Scan / Paper-Code Trace / External Signal / Pitfall Review] | `projects/[project]/evidence-packets/[run]/[packet].md` | [结论] | [promote / static_precheck / narrow / drop] | [是/否；原因] |

## 对候选 Idea 的影响

| idea | 支持 packet | 反对 / 风险 packet | 当前处理 |
|---|---|---|---|
| [idea title] | [packet-slug] | [packet-slug] | [promote / static_precheck / narrow / drop] |

## 冲突与缺口

| 问题 | 涉及 packet | 如何处理 |
|---|---|---|
| [证据冲突或缺口] | [packet-slug] | [打开原始来源 / 补一个 packet / 先标低置信度] |

## 主 Agent 合成规则

- 优先读取 packet 和本索引，不直接加载原始论文、README 或源码。
- 只有当 packet 之间冲突、关键证据缺失、或要写正式 Decision Memo 时，才打开原始来源。
- Idea Cards 的 `seed evidence`、`traceability`、`hidden pitfall` 应引用 packet，而不是堆原始材料。
