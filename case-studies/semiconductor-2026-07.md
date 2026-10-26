# Case Study: A Semiconductor Research Run (14 July 2026)

**Historical real-data workflow evidence · not a synthetic demo · not an audited investment report**

This case documents a **historical local execution** of AI Research Agent using the A-share semiconductor industry. It is a concise review of artifacts retained from July 2026, **not** a re-run of current financial APIs and not a reproduction of the original report.

## What was recorded

| Item | Evidence from the retained local artifacts |
| --- | --- |
| Industry | A-share semiconductor / 半导体 |
| Execution date | 2026-07-14; generated report timestamp 12:27:56 (local time recorded by the application) |
| Run identifier | `20260714_122550` |
| Historical mode | `AI 自动` (application history label) |
| Total runtime | 126.4 seconds in the history index |
| Inputs | Market prices, financial information, company announcements, news |
| Data-source status | All four categories marked “success” by the application |
| Output | A Markdown sector research report, about 22 KB |
| Research coverage claimed in the report | 15 sampled companies; industry overview, peer comparisons, valuations, risks and opposing arguments |

The history index records that the application ran and generated a report. The accompanying report includes market and company figures, prose analyses, source labels and an execution appendix. These are stronger evidence of prior use than a purely synthetic frontend, but **not a packet-level record of every successful API call** or independent validation of its financial claims.

## How the research pipeline operated

The historical report's execution appendix contains **three recorded stages**:

| Stage | Recorded duration | What the stage covered |
| --- | ---: | --- |
| 1. Data collection | 3.8 s | Assemble data from the four provider categories |
| 2. Industry overview | 37.9 s | Generate industry-structure analysis |
| 3. Company deep dive | 36.3 s | Compare sampled companies and indicators |

The total of these appendix timings is **78.0 seconds**, which differs from the **126.4 seconds** in the run-history index. The retained material does not reconcile that discrepancy.

The current architecture defines a **four-stage workflow**, with investment thesis as the fourth stage. **The historical July 14 artifact does not show a separately executed fourth stage.** Its risks and counterarguments appear in the report's prose, but should not be mistaken for a separate verified stage completion.

## Data sources and AI involvement

The report attributes financial inputs to **BaoStock**, market inputs to **Tencent Finance / Sina Finance / BaoStock**, public filings to **CNINFO (巨潮资讯)** and news to publicly available finance coverage aggregated through **AKShare**. The research code likewise contains adapters for those sources.

The archived run is labeled `AI 自动` and the report contains generated narrative analysis. This supports describing it as a **historical AI-assisted research run**. We have not recovered provider request/response logs sufficient to independently identify every model request, model version, token use or API cost.

## What the artifact revealed about research quality

Historical execution is not the same as reliable financial research. In this report, for example:

- A **negative liabilities ratio** is reported for a company and explained using a net-cash-like rationale; this explanation is not valid for the conventional liabilities-to-assets ratio. It should have triggered an exception and original-filing verification.
- The report uses **financial values across potentially inconsistent reporting periods**, making some direct comparisons unsafe without harmonization.
- The industry classification, company sample and specific news/corporate claims have **not been independently verified against primary filings**.
- The discrepancy between the history-index runtime and the appendix's stage timings means the precise performance breakdown is **not verified**.

These findings informed later safeguards in the public prototype: explicit provider/status metadata, period-aware comparisons, internal numeric-reference checks and clearer incomplete/failure states. Those checks reduce some risks but **do not certify real-world investment accuracy**.

## How to explore this project

- [Read the code and documentation](../README.md)
- [Try the publicly accessible synthetic presentation](https://away928.github.io/ai-research-agent/)
- [Inspect the current four-stage orchestration](../agent_workflow.py)
- [Review current offline acceptance scope](../V0.1_ACCEPTANCE.md)

**Reproduction boundary:** The full original July 2026 report and local history index are intentionally not republished. They can contain unverified investment assertions, personal metadata and material that was not prepared for publication. The values above are a limited, manually reviewed extract of the retained execution metadata. The public demo remains wholly synthetic.

*Research-engineering case study, not investment advice or evidence of profitable predictions.*
