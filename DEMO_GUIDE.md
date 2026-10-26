# Research Agent v0.1 — Demo guide

The [public browser demo](https://away928.github.io/ai-research-agent/) is the easiest way to showcase the project. It is a **fixed synthetic case study**, not a live financial-data or AI workflow. The [Streamlit app](https://ai-research-agent928.streamlit.app/) adds an interactive synthetic experience when its hosting access is public; private real research requires separate owner authorization per [Streamlit Deployment](STREAMLIT_DEPLOYMENT.md).

## Choose a demo path

| Path | Steps | What a visitor sees |
| --- | --- | --- |
| Browser, no setup | Open [GitHub Pages](https://away928.github.io/ai-research-agent/) | Fictional companies, four-step research flow, financial comparisons and prewritten report |
| Interactive local demo | Install requirements; run `python -m streamlit run app.py`; click “开始工作流演示” and advance one stage at a time | Four progressively revealed synthetic research stages; final report downloads only in the delivery step |
| Private data collection | After server authorization, select “真实研究” and an industry | Attempt to retrieve available public finance data; **not** an AI investment conclusion without a model |
| Private model-assisted research | Enable private access and configure a supported LLM provider yourself | Attempts the model-assisted pipeline; may incur fees and requires independent validation |

The static demo can also be exported locally:

```bash
python scripts/export_demo.py
```

This produces an offline HTML file under `demo_output/`. Generated files are not included in a clean clone.

## Interactive Streamlit step order

1. **数据采集** — source provenance and the fictional input snapshot.
2. **行业全景** — industry structure and explicit assumptions.
3. **公司深度** — two-company comparison with financial period warnings.
4. **投资研判** — thesis, counterarguments (Red Team) and risk checks.
5. **报告交付** — complete Markdown report and HTML download; detailed evidence/limitations in optional expanders.

Only one stage is shown at a time. Use “上一阶段” / “下一阶段” to navigate. The step indicator reflects **navigation through a prewritten demonstration**, not live model execution. The offline static GitHub Pages demo remains a separate presentation and has not been changed by this interface update.

## A three-minute walkthrough

**First minute — research flow:** explain the four stages from data collection through an industry view and company comparison to report drafting. Do **not** describe the static animation/text as live model reasoning.

**Second minute — the example:** compare the two fictitious firms' ROE, margins and growth metrics. Explain that values are synthetic; metrics from different reporting quarters must not be averaged without context.

**Third minute — evidence and handoff:** point to reporting-period fields, internal FIN reference markers, risks and the full report. An internal reference marker checks agreement with the example's input snapshot; it is not proof against an official annual report.

## Claims you should not make

- The public HTML does **not** query real finance APIs or paid LLMs.
- The Streamlit simulation and mocked CI tests do **not** validate live providers or the accuracy of investment recommendations.
- An available provider value may be late or incorrect; users must verify primary filings and definitions.
- Do not upload client or private research material without permission.

For setup, use [README](README.md). For testing methodology, use [v0.1 Validation](V0.1_ACCEPTANCE.md). Public feedback goes to [Issues](https://github.com/Away928/ai-research-agent/issues).
