# Evidence Packet：[packet title]

**项目编号**：[project-slug]  
**运行编号**：[run-slug]  
**子任务**：[Seed Scan / Paper-Code Trace / External Signal / Pitfall Review / Novelty Probe / Kill Test Design]  
**负责人**：[main-agent / subagent nickname]  
**生成时间**：[YYYY-MM-DD HH:mm]  
**上下文预算**：[目标 400-800 中文字；除表格外不粘贴长原文]  

## 问题

**本 packet 只回答一个问题**：[写清单一问题，例如“这些 seed 论文背后的代码库是否可追踪？”]

## 范围

| 项目 | 内容 |
|---|---|
| 包含 | [最多 3-8 个论文/仓库/信号源] |
| 不包含 | [不复现、不全量读源码、不写 Decision Memo、不做训练计划] |
| 停止条件 | [发现足够支持 promote/drop/narrow 的证据即停止] |

## 关键发现

| 发现 | 证据 | 对 idea 的影响 | 置信度 |
|---|---|---|---|
| [发现 1] | [链接、文件路径、指标或短证据] | [promote / static_precheck / narrow / drop] | [high / medium / low] |
| [发现 2] | [证据] | [影响] | [置信度] |

## 负面证据与坑位

| 坑位 | 预警信号 | 建议处理 |
|---|---|---|
| [A+B / 无指标 / 代码不可追踪 / 赛道拥挤 / hype] | [证据] | [drop / narrow / 先补证 / kill test] |

## 可复用证据索引

| 类型 | 标识 | 链接或路径 | 备注 |
|---|---|---|---|
| paper | [title / arXiv] | [URL] | [为什么相关] |
| repo | [owner/repo] | [URL] | [代码/数据/eval 信号] |
| signal | [GitHub / alphaXiv / HN / manual] | [URL/path] | [指标] |

## 给主 Agent 的结论

**一句话结论**：[该证据包如何改变候选 idea 的优先级。]

**建议动作**：[promote / static_precheck / narrow / drop]

**下一步最低成本检查**：[一个具体检查，不超过 2 小时或 0 GPU，除非另有 gate]
