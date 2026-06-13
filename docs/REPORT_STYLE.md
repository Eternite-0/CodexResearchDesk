# 报告文风与术语规范

## 目标

CodexResearchDesk 的正式研究交付物默认面向导师、合作者和未来复盘，因此必须先保证可读性。中文研究请求应生成中文报告，避免“中文论述 + 英文模板骨架 + 英文行动项”的混杂风格。

## 中文优先规则

- 标题、章节名、表头、列表标签、风险原因、下一步行动和正文叙述使用中文。
- 保留必要英文标识：论文标题、模型名、数据集名、指标缩写、代码路径、命令、JSON 键名、gate 枚举值。
- 缩写第一次出现时在“术语口径”中定义；之后稳定使用缩写，不反复中英文切换。
- JSON 的机器字段名和枚举值保持英文；`allowed_next_actions`、`blocking_reasons` 等人类可读字段跟随报告语言。
- 不把 `benchmark`、`baseline`、`faithfulness`、`grounding`、`kill test` 等词作为默认中文表达；优先写“基准”“基线”“忠实性”“证据锚定”“淘汰测试”。

## Decision Memo 标准栏目

中文 Decision Memo 使用以下栏目：

1. 执行结论
2. 术语口径
3. 前提校验
4. 一阶拆解
5. 多视角判断
6. 证据台账
7. 批判性评估
8. 最低成本淘汰测试
9. 资源预算
10. 最终门控
11. 自我审计

## 交付前检查

```powershell
python .\tools\check_report_style.py .\projects\<project-slug>\decisions\<idea-slug>\DECISION_MEMO.md
```

该检查只负责发现常见英文模板残留；它不能替代事实核验、引用核验或 PDF 视觉检查。
