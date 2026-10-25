# Research Agent v0.1 — Demo guide

The [public browser demo](https://away928.github.io/ai-research-agent/) is the easiest way to showcase the project. It is a **fixed synthetic case study**, not a live financial-data or AI workflow.

## Choose a demo path

| Path | Steps | What a visitor sees |
| --- | --- | --- |
| Browser, no setup | Open [GitHub Pages](https://away928.github.io/ai-research-agent/) | Fictional companies, four-step research flow, financial comparisons and prewritten report |
| Interactive local demo | Install requirements; run `python -m streamlit run app.py`; select “体验演示” | Streamlit charts/tables, the synthetic four-stage example and downloads |
| Local data collection | Select “真实研究” and an industry | Attempt to retrieve available public finance data; **not** an AI investment conclusion without a model |
| Model-assisted research | Configure a supported LLM provider yourself | Attempts the model-assisted pipeline; may incur fees and requires independent validation |

The static demo can also be exported locally:

```bash
python scripts/export_demo.py
```

This produces an offline HTML file under `demo_output/`. Generated files are not included in a clean clone.

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
