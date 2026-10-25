# 🧠 AI Research Agent

**从结构化数据到可审查的投资研究工作流。** 将数据采集、行业分析、公司比较和投资研判组织成四阶段过程；当前本地版本同时提供不调用模型的合成数据演示。

**版本定位：v0.1 开源预发布版；静态在线演示已开放，真实模型及金融数据仍需单独验证** · Python 3.9+（推荐 3.12）· Streamlit 1.50+ · [MIT License](LICENSE)

无需安装软件的第一种体验方式：直接打开本机生成的 `demo_output/Research_Agent_离线产品演示.html`。它是独立的固定案例展示页，不是可在线运行的 Agent。

```
📊 数据采集 → 🔍 行业全景 → 🏢 公司深度 → 📝 投资研判
```

## 🧪 v0.1｜三分钟体验 Demo（无需 API Key）

本次 **v0.1** 提供一键离线演示：打开 Streamlit 默认进入「体验演示（无需配置）」。

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

点击 **「▶ 一键体验完整研究 Demo」**，即可查看虚构行业的四阶段流程、合成财务对比、风险分析及完整 Markdown 报告。页面还提供**独立 HTML 下载**：下载后直接用浏览器打开，收件人无需安装环境，也不需要配置账户。

也可以直接在本机生成独立文件：

```bash
python scripts/export_demo.py
# 输出到 demo_output/Research_Agent_离线产品演示.html
```

提示：目前界面最早验收的 Streamlit 版本为 **1.50**（Python 3.9）；早于此版本的 Streamlit 可能不支持页面布局和下载参数。如已安装旧版，请按 `requirements.txt` 升级，而不是只运行旧的 `streamlit` 命令。

这份 HTML 包含自带样式的产品概览、公司指标与报告附录，不加载远程脚本、字体或数据；仅包含虚构公司及合成数字。**分享 HTML 仅能展示预设案例，不能让收件人执行真实 AI 研究。**

这条路径复用 `tests/fixtures/synthetic_research_package.json`，没有金融 API 请求、没有模型调用、没有费用，也不会生成真实研究历史。无需填写 API Key。跨季度的财务增长指标不强行计算平均值。

切换到「🔬 真实研究（使用数据源）」才会进入原来的行业选择、文件上传及研究工作流。真实研究可能受网络、数据源与模型配置影响，其输出仍需独立核验。

**公开演示已上线 GitHub Pages**：https://away928.github.io/ai-research-agent/ 。这是完全虚构数据的独立 HTML，不提供真实 AI 研究功能。原 Streamlit 网址目前需要登录，不能作为免登录公开演示；也不要把合成数据当成真实市场事实。

**介绍用的三分钟讲解路线：** [DEMO_GUIDE.md](DEMO_GUIDE.md)。其中说明如何在不暴露用户资料、不调用付费模型的情况下演示四阶段工作流。

**v0.1 交付验收：** [V0.1_ACCEPTANCE.md](V0.1_ACCEPTANCE.md)。依赖安装完成后运行 `python scripts/verify_v01.py`，即可一次检查离线单元测试、两种网页入口、CLI 和 HTML 导出。该验收不访问付费模型或真实金融 API，也不等于经过真实投资数据或模型的生产级验证。

#### 演示验收（可复现）

```bash
python -m pytest tests/test_demo_experience.py tests/test_demo_export.py -q
python scripts/verify_demo.py
```

第一条命令校验纯合成示例、四阶段内容和 Markdown 报告；第二条使用 Streamlit 的页面测试框架检查**首页、演示按钮、完整报告可见性及真实研究入口**。网页测试并不触发在线研究，也不检查真实供应商数据。完整 Markdown、独立 HTML 的下载按钮会在演示启动后直接显示于「演示成果总览」顶部；完整报告也可在「03 · 完整报告」页签阅读。




## 🔬 真实研究模式（本地安装版）

在首页选择 **「真实研究（使用数据源）」** 后，先选行业，开始按钮才会启用。

- **没有配置模型密钥**：只运行数据采集阶段，尝试获取实际可用的行情、财务、公告和新闻；没有可用观测时会停止并提示。正常结束后会生成**可下载的 Markdown 数据采集简报**（来源状态、行情/财务样本、报告期与公告新闻列表），在当前会话的结果区保留。**不会**生成 AI 投资研究报告；简报不是买卖建议，也不把上传材料的正文或文件名自动写进去。若要打印各阶段 Prompt 模板，请使用 CLI 原有降级流程。
- **已配置模型密钥**：进入四阶段研究。网页会提示第三方模型调用可能产生费用，密钥已填写**不代表**网络、余额或模型可用性已验证；成功后可下载带来源说明、财务对照与附录的完整 Markdown。
- **执行失败**：显示失败阶段和检查建议，不把不完整流程标记为成功；重新运行时不沿用上一次成功的报告。
- **保持结果**：当前会话中即使 Streamlit 重新渲染，最近一次的结果仍可查看；不会自动创建分享链接，也不承诺长期云端保存。

安全注意：API Key 环境变量只在服务端读取，不预填到浏览器。手动输入的 Key 仅作为当前会话的模型配置使用；如选择上传补充资料，部分内容可能发送给选定的第三方模型服务。不要上传无授权的研究纪要或个人敏感文件。真实数据及 AI 分析均需人工审查。

真实研究网页入口测试（使用完全虚构的引擎，不访问金融 API 和模型）：

~~~bash
python -m pytest tests/test_collection_brief.py tests/test_research_result.py -q
python scripts/verify_real_entry.py
~~~

采集后的图表和数据卡片属于可选的展示组件；如果某一展示组件异常，网页保留采集简报及其下载能力，并提示哪类视图无法展示，而不会错误地宣布整个数据采集失败。本地历史索引写入也是非关键步骤：如果目录不可写，网页会提示，但不影响当前会话中的研究简报或完整报告下载。

## ✨ 核心特性

### 🔬 五维数据采集（全部免费，无需付费终端）

| 维度 | 数据源 | 说明 |
|------|------|------|
| **行情** | 腾讯财经 + 新浪财经 + baostock | 尝试在线获取，需核对实际交易日与延迟 |
| **财务** | baostock 季频财务接口（待原始财报核验） | ROE / 毛利率 / 营收增速 / 净利增速 / 负债率 |
| **公告** | 巨潮资讯网 | 成分股公司最新公告，覆盖前 10 家公司 |
| **新闻** | AKShare 聚合公开财经媒体 | 公司新闻 + 行业关键词搜索，含情感标注 |
| **用户** | 上传 .md / .txt / .pdf / .docx | 会议纪要 / 专家访谈 / 调研笔记 |

每个数据源独立降级：`在线 → 缓存(7天) → 空`，不做假兜底。

### 🧠 四阶段 AI 投研工作流

| 阶段 | 功能 | 输出 |
|------|------|------|
| 📊 数据采集 | 五维数据自动采集（纯 Python） | 行情卡片 + 财务表格 + Altair 图表 |
| 🔍 行业全景 | 产业链梳理、增长趋势、竞争格局、政策技术 | 2500-3500 字分析报告 |
| 🏢 公司深度 | 集中度/头部对比/盈利质量/估值/预警 | 含对比表格的分析报告 |
| 📝 投资研判 | 周期判断、可跟踪信号、风险识别、Red Team | 最终投资研究报告 |

每个阶段报告均在网页中实时展示，支持独立下载。

### 🌐 已覆盖 15 个行业

| AI与科技 | 先进制造 | 消费与金融 | 医疗健康 |
|------|------|------|------|
| AI算力、人工智能、信息技术 | 机器人、工业4.0 | 消费、金融科技 | 生物医药、医药健康 |
| 移动互联网、智能汽车、半导体、新硬件 | 新能源汽车、能源金属 | | |

成分股尝试通过新浪概念板块 API 获取并按流通市值排序；来源可能不可用或发生数据延迟。

### 🖥️ Streamlit Web 界面

Terminal Blue 专业深蓝风格，Pipeline 时间轴可视化（实时耗时），历史研究记录，数据卡片 + 交互图表。每阶段报告在网页中直接可读。

### 🔄 智能降级 + 质量保障

- **有 API key** → 四阶段 AI 全自动完成
- **无 API key** → Python 数据采集正常运行 + 打印 Prompt 模板供手动使用
- **上下文安全** → tiktoken 自动计数，超出上限智能压缩
- **输出格式提示（非事实核验）** → 检查数字样式、数据源名称、章节与风险标记；缺失时可追问补全。**不会**确认数字真实性、来源是否支持结论或投资判断正确性，所有报告需独立核验。

---

## 🚀 快速开始

### 🌐 公开在线演示（无需登录）

👉 **[Research Agent v0.1 静态展示页](https://away928.github.io/ai-research-agent/)**

该页面已通过公开网页访问测试。内容全部为**固定合成数据**，可用于产品展示，不运行 Python、外部金融接口或模型。真实可交互的 Streamlit 应用请使用本地运行方式。

此前的 [Streamlit Cloud 地址](https://ai-research-agent928.streamlit.app/) **目前要求登录**；是否向匿名访客开放，需在对应 Streamlit Cloud 管理界面调整应用可见性后单独验收。

### 💻 本地开发

```bash
git clone https://github.com/Away928/ai-research-agent.git
cd ai-research-agent
pip install -r requirements.txt
```

#### 命令行

```bash
# 降级模式（无需 API key）— 数据采集 + 打印 Prompt 模板
python cli.py --industry "AI算力"

# DeepSeek 后端（国内推荐，性价比高）
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
python cli.py --industry "AI算力"

# Anthropic 后端
export ANTHROPIC_API_KEY="sk-ant-xxx"
python cli.py --industry "AI算力"

# 其他 OpenAI 兼容后端（千问 / 豆包 / GPT 等）
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://your-api-endpoint/v1"
export OPENAI_MODEL="your-model-name"
python cli.py --industry "AI算力"
```

输出文件在 `demo_output/` 目录下。

---

## 📊 多模型后端支持

| 后端 | 适用模型 | 配置方式 |
|------|---------|---------|
| **OpenAI 兼容** | DeepSeek / 千问 / 豆包 / GPT | 设置 `OPENAI_API_KEY` + `OPENAI_BASE_URL` |
| **Anthropic** | Claude 系列 | 设置 `ANTHROPIC_API_KEY` |

Web 界面中两种后端均可在侧边栏直接配置。

---

## ⚙️ 高级配置

所有参数通过环境变量覆盖（详见 `config.py`）：

```bash
export AGENT_MAX_CONSTITUENTS=30    # 成分股数量（默认 20）
export AGENT_CACHE_DAYS=14          # 缓存天数（默认 7）
export AGENT_HTTP_TIMEOUT=15        # HTTP 超时（默认 10s）
export AGENT_TEMPERATURE=0.5        # LLM temperature（默认 0.3）
```

---

## 📁 项目结构

```
ai-research-agent/
├── app.py                           # Streamlit Web 界面
├── cli.py                           # CLI 入口
├── agent_workflow.py                # 4 阶段工作流编排
├── agent_helpers.py                 # AI 调用编排（重试/校验/压缩）
├── llm_client.py                    # 多模型 LLM 客户端
├── config.py                        # 集中配置
├── prompts/                         # Prompt 模板 + 校验
├── ui/                              # Web UI 组件
├── tools/
│   ├── data_sources/                # 数据源（行情/财务/公告/新闻）
│   └── cache/                       # 本地缓存
├── utils/token_counter.py           # tiktoken 计数 + 上下文压缩
├── demo_output/                     # 输出报告 + 历史索引
├── requirements.txt
└── README.md
```

---

## 🧭 设计理念

**不是"替代人"，是"放大人"。**

```
        AI 负责（数据采集 + 分析 + 报告）
  数据采集 → 结构化提取 → 多维度对比 → 报告生成
              │
              ▼
        ┌─────────────┐
        │ 人机交叉区    │
        │ 投资机会初筛   │
        │ 数据验证      │
        └──────┬──────┘
              │
              ▼
      人类负责（20% 工作量）
  最终决策 管理层评估 择时判断 反事实推理
```

三个核心原则：
1. **不做假兜底** — 没有的数据诚实说没有，不拿过时数据冒充
2. **数据要流到需要它的地方** — 所有阶段都能访问完整数据包
3. **让 AI 引用真实数字，不编造** — 传给 AI 的是结构化 JSON，不是纯文本

---

## ❓ FAQ

<details>
<summary><b>没有 API key 能跑吗？</b></summary>

能。降级模式下数据采集正常运行，所有 Prompt 模板打印到终端，可手动复制到任何 AI 工具使用。

</details>

<details>
<summary><b>成分股是动态的吗？</b></summary>

优先使用新浪概念板块 API 获取成分股；实际覆盖与时效需以当次返回结果核对，不应视为始终实时。

</details>

<details>
<summary><b>支持哪些行业？</b></summary>

当前支持 15 个行业，与新浪热门概念板块一一映射。在 `market_sources.py` 的 `_SINA_CONCEPT_NODE_MAP` 中加入新的行业名 → 概念板块 Node ID 即可扩展。

</details>

<details>
<summary><b>财务数据为什么有些公司缺失？</b></summary>

财务数据尝试使用 baostock 财务接口，并可降级使用本地缓存。不同指标可能来自不同季度；当前会分别记录其报告期，缺失或无法确定时标为未知，不能以采集日期代替。

</details>

---

## 数据来源对照与核查边界

- 每次采集会保留来源核查元信息；财务指标还会尽可能记录每项实际报告期。
- 研究报告附录会列出本次采集的财务数字、报告期、来源标签与内部记录 ID（如 `FIN-000001-roe_pct`），供人工回查。
- 内部 ID 只是本次数据包的索引，**不是原始公告链接，也不能证明数字真实或正文结论有证据支持**。缓存可能缺少完整上游来源；无法判断的报告期保持未知。
- 现有测试可用 `python -m pytest -q` 离线执行单元检查；这不包含实时金融 API、付费 LLM 或端到端投资判断正确性验收。

## 无网络、无付费模型的完整流程验收

```bash
python -m pytest tests/test_offline_research_workflow.py -q
```

该测试使用 `tests/fixtures/synthetic_research_package.json` 内的虚构公司与财务数据、预设的模型输出，以及临时输出目录。它会实际跑完四个工作阶段，并检查报告中一条故意不一致的财务引用；**不是**真实数据源或真实 LLM 的端到端验证。

## baostock 财务字段校验

对照 [baostock API 文档](https://github.com/zxygithub/baostock/blob/master/docs/pythonAPI.md) 并通过 baostock 0.9.4 的只读历史查询核实返回字段：

- ROE 使用 `profit.roeAvg`，毛利率使用 `profit.gpMargin`。
- 净利润同比使用 `growth.YOYNI`，**不能把 `YOYEquity`（净资产同比）当作营收增速**。
- 资产负债率使用 `balance.liabilityToAsset`，不能从杜邦接口的固定列号猜取。
- `revenue_growth_pct` 代表**主营业务收入（MBRevenue）同报告季度同比**，只有本期与上年同季度金额均有效且分母大于零才计算，不能混同为营业总收入同比。
- 查询结果严格按字段名、统计期与已知披露日期检查；旧版本财务缓存与新字段口径不兼容，会自动忽略，改由在线接口或新版本缓存重建。所有历史 AI 报告里的相关数字应重新计算，不能继续作为可信数据使用。

这只是字段和计算逻辑验证，不能代替与交易所或上市公司原始财报逐项对账。

## 官方财报基准与供应商对账

已在 `tests/fixtures/primary_filing_600519_2025h1.json` 记录**贵州茅台（600519）2025年半年报**中的真实财务披露数据，来源：[上交所原始报告 PDF](https://big5.sse.com.cn/site/cht/www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2025-08-13/600519_20250813_TU6Y.pdf)。独立测试通过财报原始人民币金额计算出：营业收入同比 9.10%、归母净利润同比 8.89%、按营业收入/营业成本计算的毛利率 91.30%、按合并资产负债表计算的负债率 14.75%；原报表列示加权平均 ROE 17.89%。基准保留了页码和具体计算原料，可用以下命令复核：

```bash
python -m pytest tests/tools/data_sources/test_primary_filing.py -q
```

`tools.data_sources.provenance.compare_filing_benchmark(provider_record, official_fixture)` 可对随后采集的供应商快照进行保守比较，默认资产负债率容差为 **0.05 个百分点**，并核对股票代码、期间及 `balance.liabilityToAsset` 字段。**这只比较数值，不验证供应商数据来源或合并报表口径**。其他四项指标因为定义不完全一致，暂标为 `definition_not_yet_verified`，不能用“恰好相等”代替审计。2026-10-24 再次尝试连接 baostock 时登录超时，因此**尚无 600519 该季度的已核实实时供应商快照**，不能宣称完成源头到报告的全面数值级对账。

## 财务数字引用对账（有限范围）

报告正文可使用形如 `[[FIN-000001-roe_pct=8.0]]` 的财务记录标记。系统仅对照**本次采集快照**中的股票代码、指标和数值，报告附录会列出匹配、冲突、格式错误或缺少引用的情况。没有标记不能算作检查通过；即使标记匹配，也**不证明**外部数据真实、正文语义正确或结论可靠。聚合值仍需人工复算。

## 研究失败与自动化调用

无论 CLI 还是 Streamlit 网页入口，任一研究阶段发生异常后都会停止依赖它的后续阶段，不能将缺少上游依据的结果称为完成。CLI 返回非零退出码，工作日志记录失败阶段及跳过的阶段；在 AI 模式下，如果分析正文为空，程序也会拒绝将其作为完成报告。四类数据源均无有效观测、且没有用户补充材料时，同样停止后续分析。财务查询严格按允许披露的季度从新到旧进行，各指标独立回溯，并保留各自报告期；缓存只匹配完整行业名称。

## 开源发布安全门槛

在考虑更新公开仓库或发布新版本前，先执行只读路径排查：

```bash
python3 -m tools.release_safety
```

当前公开 `main` 为重新建立的干净 Git 历史，不包含以前跟踪的 `user_data/` 研究资料、生成报告和本机配置。但**旧 SHA 可能仍被 GitHub 缓存或既有克隆访问**；这不是换根提交就能保证消失的。历史文件仍需要单独核对来源、授权及可见性。路径检查不会扫描所有秘密，不能替代内容级审查。

## ⚠️ 局限性

- 研报暂无免费在线源，公告和新闻可作为部分替代
- AI 在不确定时倾向于编造而非承认不知道 — 所有分析需人工验证
- 仅基于公开信息，无法获取一手调研数据
- 报告中包含的投资分析**不构成投资建议**

---

## 维护与许可证

本项目由 LICENSE 中列示的作者维护，按 MIT License 发布。请通过未来发布仓库的 Issues 反馈问题。
