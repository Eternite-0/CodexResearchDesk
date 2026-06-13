# 视觉-语言工业异常检测研究笔记

## 主题

基于视觉-语言模型的工业异常检测与缺陷解释。

## 当前门控

- 项目：`vlm-industrial-anomaly`
- 想法：`vlm-iad-defect-explanation`
- 结论：`STATIC_ONLY`
- 备忘录：`projects/vlm-industrial-anomaly/decisions/vlm-iad-defect-explanation/DECISION_MEMO.md`

## 工作假设

**泛泛的视觉-语言工业异常检测方法新意不足；更可能成立的贡献点是“证据锚定的缺陷解释”：把异常区域、缺陷类型、制造过程知识和解释忠实性评价绑定在一起。**

## 需要复核的关键近作

| 工作 | 链接 | 相关性 |
|---|---|---|
| WinCLIP | https://arxiv.org/abs/2303.14814 | CLIP 零/少样本异常分类与分割基线。 |
| AnomalyGPT | https://arxiv.org/abs/2308.15366 | 早期基于大视觉-语言模型的工业异常检测，对话与文本描述能力直接相关。 |
| AnomalyCLIP | https://arxiv.org/abs/2310.18961 | 对象无关提示学习，用于零样本异常检测。 |
| Myriad | https://arxiv.org/abs/2310.19070 | 用工业异常检测视觉专家引导多模态模型。 |
| FADE | https://arxiv.org/abs/2409.00556 | 面向分割的 CLIP 零/少样本适配方法。 |
| MMAD | https://arxiv.org/abs/2410.09453 | 多模态大模型工业异常检测基准，显示当前模型仍低于工业要求。 |
| Echo | https://arxiv.org/abs/2501.15795 | 多专家指导的多模态工业异常检测方法。 |
| LogicQA | https://arxiv.org/abs/2503.20252 | 用问题清单解释逻辑异常。 |
| Triad | https://arxiv.org/abs/2503.13184 | 制造过程感知的多模态异常检测。 |
| ADSeeker | https://arxiv.org/abs/2508.03088 | 知识锚定、检索增强和异常推理。 |
| MMR-AD | https://arxiv.org/abs/2604.10971 | 大规模多模态基准和推理式异常检测模型。 |

## 未解决缺口

- 需要一个可辩护的工业缺陷解释忠实性指标。
- 需要与 Triad、ADSeeker、LogicQA、MMR-AD 做直接差异比较。
- 训练前必须先有静态审计协议。
