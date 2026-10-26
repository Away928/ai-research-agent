# AI Research Agent

**An early-stage, evidence-aware workflow for investment research — from data collection to a reviewable report.**

[Try the public demo](https://away928.github.io/ai-research-agent/) · [v0.1.4 release](https://github.com/Away928/ai-research-agent/releases/tag/v0.1.4) · [MIT License](LICENSE) · [中文简介](#中文简介)

> **Demo-ready MVP, not an autonomous investment adviser.** The public demo uses **synthetic companies, synthetic data, and prewritten analysis**. It neither runs a live model nor retrieves real market data. The Streamlit interface is **synthetic-only by default**; private live research requires a server-side opt-in and independent access credential.

**Interactive Streamlit app:** [ai-research-agent928.streamlit.app](https://ai-research-agent928.streamlit.app/) — once the hosting owner sets its Cloud **Sharing** setting to public, visitors can run the synthetic demo without signing in. The code itself is already safe-by-default; the hosted app's sharing status must be checked separately. See [Streamlit deployment and private-mode security](STREAMLIT_DEPLOYMENT.md).

## See it first — no setup

**[Open the static demo →](https://away928.github.io/ai-research-agent/)**

Explore an example four-stage research narrative, two fictional companies, comparative financial tables, risks, and a downloadable report. The site is a standalone HTML presentation, open without an API key or account.

To explore the **interactive** offline demo on your computer, run Streamlit as described below. The Streamlit Cloud sharing state must be verified independently in an unauthenticated session; the static demo remains an always-public fallback.

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

AI Research Agent 是一个将**公开数据采集、行业梳理、公司对比和研究报告**组织成四阶段流程的开源原型。

- **无需安装的在线体验**：打开 [公开静态演示](https://away928.github.io/ai-research-agent/)。其中的公司、财务数字和分析文字均为**虚构/合成**，不是实时模型结果。
- **本地交互演示**：安装 `requirements.txt` 后运行 `python -m streamlit run app.py`，点击「开始工作流演示」，按数据采集 → 行业全景 → 公司深度 → 投资研判 → 报告交付逐步体验。
- **尝试真实研究**：仅在服务端显式启用并通过私人凭证验证后，才能选择「真实研究」；无模型 Key 只尝试生成数据采集简报，有 Key 才尝试 AI 分析，可能产生费用。
- **质量边界**：197 项离线测试通过；真实数据源与付费模型的全流程准确性、稳定性和投资有效性尚未验证。

报告中任何数据和结论都需要回查原始披露，**不构成投资建议**。欢迎通过 GitHub Issues 反馈可以复现的问题。
