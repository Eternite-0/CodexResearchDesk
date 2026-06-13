# Idea Sprint：[主题 / 方向]

**项目编号**：[project-slug]  
**日期**：[YYYY-MM-DD]  
**目标**：从论文、代码库、外部信号和领域痛点中产出可做的研究 idea，并提前避开明显坑位。  

## 输入材料

| 类型 | 内容 | 用途 |
|---|---|---|
| 论文 / arXiv | [标题、arXiv ID、链接] | [作为 seed / baseline / 反例 / 相邻工作] |
| 代码库 | [owner/repo] | [判断工程可接住性，不做复现] |
| 外部信号 | [GitHub / alphaXiv / HN / HF / Reddit / X / 企业采用] | [判断热度、拥挤度、真实需求或 hype 风险] |
| 领域痛点 | [实际未解决问题] | [避免为了组合而组合] |

## Evidence Packets

主 Agent 只汇总证据包，不把论文全文、README 全文或源码塞进上下文。

| packet | 子任务 | 负责人 | 路径 | 对候选的影响 |
|---|---|---|---|---|
| [packet-slug] | [Seed Scan / Paper-Code Trace / External Signal / Pitfall Review] | [subagent / main-agent] | `projects/[project-slug]/evidence-packets/[run-slug]/[packet-slug].md` | [promote / static_precheck / narrow / drop] |

**要求**：每个候选 idea 的 `seed evidence`、`traceability`、`hidden pitfall` 至少引用一个 packet。没有 packet 时，必须说明“未分块取证，本轮为轻量草案”。

## 候选 Idea 总表

| 排名 | idea | 初步动作 | 为什么值得想 | 最大坑位 | 最低成本 kill test |
|---:|---|---|---|---|---|
| 1 | [idea title] | [promote / static_precheck / narrow / drop] | [价值] | [坑] | [0-GPU 或最低成本检查] |
| 2 | [idea title] | [promote / static_precheck / narrow / drop] | [价值] | [坑] | [检查] |
| 3 | [idea title] | [promote / static_precheck / narrow / drop] | [价值] | [坑] | [检查] |

## Idea Cards

### Idea 1：[标题]

| 字段 | 内容 |
|---|---|
| core claim | [一句可证伪主张] |
| seed evidence | [来自哪些论文、仓库、benchmark、外部信号或失败经验] |
| mechanism / insight | [不是堆方法，而是哪个机制或问题重构可能成立] |
| why not A+B | [说明它不是“论文 A + 论文 B”的直接拼接] |
| avoided pitfall | [它主动避开的已知死路] |
| hidden pitfall | [最可能让它失败的坑] |
| traceability | [关键论文/基线是否有代码、数据、checkpoint、eval 脚本或指标] |
| falsifier | [什么观察会让它停止或收窄] |
| lowest-cost kill test | [0-GPU 或最低成本检查] |
| action | [promote / static_precheck / narrow / drop] |

### Idea 2：[标题]

| 字段 | 内容 |
|---|---|
| core claim | [一句可证伪主张] |
| seed evidence | [证据] |
| mechanism / insight | [机制] |
| why not A+B | [非 A+B 说明] |
| avoided pitfall | [避开的坑] |
| hidden pitfall | [隐藏坑] |
| traceability | [代码/数据/指标可追踪性] |
| falsifier | [推翻条件] |
| lowest-cost kill test | [最低成本检查] |
| action | [promote / static_precheck / narrow / drop] |

## 避坑台账

| 坑位 | 涉及 idea | 预警信号 | 处理方式 |
|---|---|---|---|
| A+B 包装 | [idea] | [没有新机制/新问题/新评价] | [drop / narrow / 补查最近工作] |
| 无指标 | [idea] | [没有固定 benchmark、trace、metric] | [先定义静态指标或停止] |
| 代码不可追踪 | [idea] | [无 repo / code coming soon / unofficial / 缺 eval] | [先做 paper-code scout] |
| 赛道拥挤 | [idea] | [近作太多且差异小] | [找更窄切口或停止] |
| hype 先于证据 | [idea] | [热度高但无 benchmark/企业采用/复现实证] | [先找负面 issue 和失败报告] |

## 下一步

**只推进 1-3 个候选。**  

| 优先级 | idea | 下一步 | 不做什么 |
|---:|---|---|---|
| 1 | [idea] | [Direction Brief / paper-code scout / kill test] | [不训练 / 不扩写论文 / 不复现] |
| 2 | [idea] | [下一步] | [不做什么] |
| 3 | [idea] | [下一步] | [不做什么] |
