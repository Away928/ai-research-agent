# AI Research Agent

**An early-stage, evidence-aware workflow for investment research — from data collection to a reviewable report.**

[Try the public demo](https://away928.github.io/ai-research-agent/) · [v0.1.4 release](https://github.com/Away928/ai-research-agent/releases/tag/v0.1.4) · [MIT License](LICENSE) · [中文简介](#中文简介)

> **Demo-ready MVP, not an autonomous investment adviser.** The public demo uses **synthetic companies, synthetic data, and prewritten analysis**. It neither runs a live model nor retrieves real market data. The Streamlit interface is **synthetic-only by default**; private live research requires a server-side opt-in and independent access credential.

**Interactive Streamlit app:** The UI is implemented and runs locally. Anonymous public access to the [hosted URL](https://ai-research-agent928.streamlit.app/) is **not verified**; use the static demo or local instructions instead. See [Streamlit deployment and private-mode security](STREAMLIT_DEPLOYMENT.md).

## See it first — no setup

**[Open the static demo →](https://away928.github.io/ai-research-agent/)**

Explore an example four-stage research narrative, two fictional companies, comparative financial tables, risks, and a downloadable report. The site is a standalone HTML presentation, open without an API key or account.

To explore the **interactive** offline demo on your computer, run Streamlit as described below. The Streamlit Cloud sharing state must be verified independently in an unauthenticated session; the static demo remains an always-public fallback.

## Real research run

**[Real-run case study: AI Compute, October 2026](case-studies/ai-compute-2026-10.md)** — four-stage local execution. Figures and investment conclusions are not independently audited.

## What the project does

```text
1. Collect market, financial, announcement and news inputs
                   ↓
2. Organize an industry overview
                   ↓
3. Compare companies and financial indicators
                   ↓
4. Draft and review an investment-research report
```

| Capability | In v0.1 | Evidence and limits |
| --- | --- | --- |
| Offline product demo | Streamlit interface plus standalone HTML | Fixed synthetic fixture; **no live AI or finance APIs** |
| Public-data collection | Attempt market, quarterly financial, announcement and news retrieval | Dependent on public providers, availability and reporting dates |
| Model-assisted analysis | Multi-stage workflow with OpenAI-compatible or Anthropic backends | Requires your own key; real-model end-to-end performance **not yet validated** |
| Provenance checks | Source/report-period metadata and internal numeric-reference consistency checks | A match does **not** verify an official filing or investment conclusion |
| Export and failure handling | Markdown results, demo HTML, and explicit failure states | Outputs still require independent human review |

The tool does **not** place orders or execute trades.

## Run locally

**Requirements:** Python **3.12 recommended** (also tested on Python 3.9 and 3.13), access to install the packages in [requirements.txt](requirements.txt). Use a virtual environment.

```bash
git clone https://github.com/Away928/ai-research-agent.git
cd ai-research-agent
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

The current public-mode code opens **directly into the synthetic walkthrough** (no needless one-option mode selector). Click **“▶ 开始工作流演示”**, then use **“下一阶段 →”** to review four research stages followed by a separate report-delivery step. Detailed evidence and the full report stay collapsed until the relevant step. This demo requires **no financial or LLM API key**.

For a standalone HTML file you can share or open offline:

```bash
.venv/bin/python scripts/export_demo.py
```

The command writes to `demo_output/`. New clones do **not** contain a pre-generated HTML file; create it with the command above.

### Use your own industry inputs

Switch to **“真实研究（使用数据源）”** in the Streamlit interface and choose an industry.

- **Access first:** Real research is not present on the public demo. An owner must separately enable and unlock it in a private deployment; follow [deployment and access instructions](STREAMLIT_DEPLOYMENT.md).
- **Without an LLM key, after private unlock:** the app attempts public-data collection and, where observations are available, prepares a **data-collection brief**, **not** a generated investment thesis.
- **With an LLM key, after private unlock:** the app attempts the model-assisted workflow. Model/API access can incur charges and fail due to authentication, network access, quotas or provider changes; success is not guaranteed.
- **With user-provided material:** only upload content that you have the right to share with a selected model or service.

The local CLI is a separate program; unlike the shared Streamlit UI it does not use the browser access gate. Use it **only on a machine you control**:


```bash
.venv/bin/python cli.py --industry "半导体"
.venv/bin/python cli.py --help
```

Optional environment-based configuration is documented in [config.py](config.py). Keep `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and other secrets out of Git, logs and public screenshots.

## Testing and evidence quality

For the complete offline regression and UI acceptance suite:

```bash
.venv/bin/python scripts/verify_v01.py
```

This includes Python tests, simulated Streamlit interactions, CLI smoke checks and HTML export verification. The current v0.1.3 code passed **197 offline tests**, including server-access regression tests and staged Streamlit UI checks. [GitHub Actions](https://github.com/Away928/ai-research-agent/actions) verifies supported Python versions and full-install smoke tests.

There is a deliberately narrow distinction between **data consistency** and **factual correctness**:

- Financial values are associated with provider/reporting-period metadata when available.
- Internal FIN reference markers help compare a report with the input snapshot.
- The project includes a limited benchmark derived from a named official filing, but that **does not** prove that every provider value or generated claim matches its original disclosure.
- Synthetic/mocked tests cannot establish real LLM accuracy, source credibility, or investment performance.

For deeper implementation and demo evidence, see [Demo Guide](DEMO_GUIDE.md) and [v0.1 Validation](V0.1_ACCEPTANCE.md).

## Repository layout

```text
app.py               Streamlit entrypoint
cli.py               Command-line entrypoint
agent_workflow.py     Four-stage workflow orchestration
llm_client.py         Model backend interface
config.py             Environment-based configuration
prompts/              Analysis prompt templates
tools/data_sources/   Financial-data providers and provenance logic
tools/demo_export.py  Standalone synthetic HTML export
ui/                   Streamlit UI components
tests/                Offline fixtures and regression tests
scripts/              Demo export and acceptance checks
```

## Safety, limitations and collaboration

This is a **research-assistance prototype**, not financial advice or a verified investment recommendation. Public sources can be missing, delayed, inconsistent or inaccurately parsed; generated text can invent numbers or misinterpret a document. **Check official filings and source timestamps before using any output.** Do not enter real client records, nonpublic material, personal identifiers or credentials into the demo.

The [static browser showcase](https://away928.github.io/ai-research-agent/) remains the always-public, zero-setup reference. The Streamlit app supports a **public interactive synthetic demo** after its Cloud sharing setting is opened, and a **separately enabled private owner research mode**. It is not a hardened multi-user service; its external data/model pipeline has not passed production-grade end-to-end evaluation. See [deployment guide](STREAMLIT_DEPLOYMENT.md).

Contributions and reproducible bug reports are welcome: [Contributing](CONTRIBUTING.md) · [Issues](https://github.com/Away928/ai-research-agent/issues) · [Security](SECURITY.md).

**License:** [MIT](LICENSE).

## 中文简介

AI Research Agent 是一个面向投资研究的开源 AI Agent，整合金融数据采集、行业分析、公司比较与投资研判，形成完整的研究工作流，并生成可供审阅的研究报告。

**真实运行案例**：[AI 算力研究（2026 年 10 月）](case-studies/ai-compute-2026-10.md)

### 研究工作流

1. **数据采集**：获取行情、财务、公告及新闻等信息。
2. **行业全景**：分析产业链、市场格局及行业发展趋势。
3. **公司深度**：比较公司的财务表现、估值与竞争地位。
4. **投资研判**：形成研究假设，分析投资机会、风险及反方观点。

**最终交付**：整合上述研究结果，生成结构化投资研究报告。

### 如何体验

- **在线交互演示**：Streamlit 交互界面已经开发，但[云端地址](https://ai-research-agent928.streamlit.app/)的匿名访问尚未验证可用；目前请使用下方本地运行方式。
- **静态演示**：[GitHub Pages](https://away928.github.io/ai-research-agent/) — 无需登录，直接浏览示例研究报告。
- **本地运行**：克隆仓库、安装依赖并运行 `streamlit run app.py`。具体步骤见上方英文使用指南。

项目支持接入公开金融数据源及大语言模型，进行实际研究。相关配置与使用说明见 [部署指南](STREAMLIT_DEPLOYMENT.md)。

*本项目用于辅助投资研究，不构成投资建议。*
