# VLM Industrial Anomaly Research Wiki

## Topic

基于视觉-语言模型的工业异常检测与缺陷解释。

## Current Gate

- Project: `vlm-industrial-anomaly`
- Idea: `vlm-iad-defect-explanation`
- Verdict: `STATIC_ONLY`
- Memo: `projects/vlm-industrial-anomaly/decisions/vlm-iad-defect-explanation/DECISION_MEMO.md`

## Working Hypothesis

**泛泛的 VLM-IAD 方法新意不足；更可能成立的贡献点是 grounded defect explanation：把异常区域、缺陷类型、制造过程知识和解释忠实性评价绑定在一起。**

## Key Prior Work To Recheck

| Work | Link | Why It Matters |
|---|---|---|
| WinCLIP | https://arxiv.org/abs/2303.14814 | CLIP zero-/few-shot anomaly classification and segmentation baseline. |
| AnomalyGPT | https://arxiv.org/abs/2308.15366 | Early LVLM-based IAD with dialogue and textual descriptions. |
| AnomalyCLIP | https://arxiv.org/abs/2310.18961 | Object-agnostic prompt learning for zero-shot anomaly detection. |
| Myriad | https://arxiv.org/abs/2310.19070 | Uses IAD vision experts to guide LMMs. |
| FADE | https://arxiv.org/abs/2409.00556 | Few-/zero-shot CLIP adaptation for segmentation. |
| MMAD | https://arxiv.org/abs/2410.09453 | MLLM benchmark showing current models remain below industrial requirements. |
| Echo | https://arxiv.org/abs/2501.15795 | Multi-expert guidance for MLLM-based IAD. |
| LogicQA | https://arxiv.org/abs/2503.20252 | Question-checklist approach for logical anomaly explanations. |
| Triad | https://arxiv.org/abs/2503.13184 | Manufacturing-process-aware LMM anomaly detection. |
| ADSeeker | https://arxiv.org/abs/2508.03088 | Knowledge-grounded RAG and anomaly reasoning. |
| MMR-AD | https://arxiv.org/abs/2604.10971 | Large multimodal benchmark and reasoning-based AD model. |

## Open Gaps

- Need a defensible explanation faithfulness metric for industrial defects.
- Need direct comparison with Triad, ADSeeker, LogicQA, and MMR-AD.
- Need a static audit protocol before any training.
