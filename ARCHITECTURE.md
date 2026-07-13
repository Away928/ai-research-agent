# AI Research Agent 架构流程图

```mermaid
flowchart TB
    subgraph Entry["🚪 入口"]
        CLI["cli.py<br/>命令行入口<br/>argparse → agent.run()"]
        Web["app.py<br/>Streamlit Web UI<br/>侧边栏 + 报告渲染"]
    end

    subgraph Agent["🧠 核心编排 — agent_workflow.py (391行)"]
        AgentClass["AIResearchAgentV2"]
        Init["__init__<br/>LLMClient + DataSourceManager<br/>+ ReportFormatter"]
        Stage0["Stage 0: 数据采集<br/>stage_context_gathering()<br/>纯 Python，不调 AI"]
        Stage1["Stage 1: 行业全景<br/>stage_industry_overview()"]
        Stage2["Stage 2: 公司深度<br/>stage_company_deep_dive()"]
        Stage3["Stage 3: 投资研判<br/>stage_investment_thesis()<br/>→ 直接输出最终报告"]
        Run["run()<br/>按序执行 4 阶段<br/>错误隔离 + 日志保存"]

        Init --> Run
        Run --> Stage0 --> Stage1 --> Stage2 --> Stage3
    end

    subgraph LLM["🤖 LLM 抽象 — llm_client.py (264行)"]
        LLMClient["LLMClient<br/>自动检测后端:<br/>Anthropic / OpenAI Compat"]
        Ask["ask(prompt, system)<br/>3次重试 + 指数退避"]
        AskLog["ask_with_log()<br/>带耗时日志"]
        LLMClient --> Ask --> AskLog
    end

    subgraph DataLayer["📊 数据采集层 — tools/data_sources/"]
        DSM["DataSourceManager<br/>__init__.py (227行)<br/>并发采集编排"]
        Market["market_data.py (202行)<br/>MarketDataSource<br/>多源行情融合"]
        Sources["market_sources.py (302行)<br/>底层 API 调用<br/>腾讯 q.gtimg.cn<br/>新浪 hq.sinajs.cn<br/>baostock<br/>akshare"]
        Financial["financial_data.py (287行)<br/>baostock 财报<br/>ROE/毛利率/增速/负债率<br/>✅ 7天缓存"]
        Announce["announcement_data.py (239行)<br/>巨潮资讯网公告<br/>✅ 7天缓存"]
        News["news_data.py (94行)<br/>AKShare 新闻<br/>❌ 无缓存(实时)"]
        Config["industry_config.py (341行)<br/>15行业骨架<br/>13新浪指数映射"]
        Summary["summary.py (266行)<br/>数据采集报告<br/>build_summary + print_summary"]

        DSM --> Market --> Sources
        DSM --> Financial
        DSM --> Announce
        DSM --> News
        Market --> Config
        DSM --> Summary
    end

    subgraph UserLayer["📁 用户数据 — tools/user_data.py (311行)"]
        UDM["UserDataManager"]
        Parse["parse_uploads()<br/>.md/.txt/.pdf/.docx"]
        SumSupp["summarize_supplements()<br/>用户补充数据摘要"]
        UDM --> Parse
        UDM --> SumSupp
    end

    subgraph ReportLayer["📝 报告 — tools/report_formatter.py (192行)"]
        RF["ReportFormatter"]
        Format["format_report()<br/>header + content + footer"]
        RF --> Format
    end

    subgraph Prompts["📋 Prompt 模板 — prompts/"]
        SysPrompts["system_prompts.py (25行)<br/>3个AI角色 system prompt"]
        P1["industry_overview.md<br/>行业全景分析<br/>变量: {{INDUSTRY}} {{DATA}}"]
        P2["company_deep_dive.md<br/>公司深度分析<br/>变量: {{INDUSTRY}} {{COMPANIES}} {{INDUSTRY_CONTEXT}}"]
        P3["investment_thesis.md<br/>投资研判+最终报告<br/>变量: {{INDUSTRY}} {{DATE}} {{CONTEXT}}"]
        SysPrompts --> P1
        SysPrompts --> P2
        SysPrompts --> P3
    end

    subgraph UI["🎨 Streamlit UI — ui/"]
        Styles["styles.py (103行)<br/>CSS + COLORS 共享颜色"]
        Sidebar["sidebar.py (125行)<br/>API配置 + 行业列表"]
        Input["input_area.py (62行)<br/>行业选择 + 文件上传"]
        Cards["data_cards.py (167行)<br/>数据展示卡片"]
        Charts["charts.py (168行)<br/>Altair 交互图表<br/>市值/PE/涨跌/ROE"]
        Welcome["welcome.py (51行)<br/>使用说明"]
        Styles -.-> Charts
    end

    %% === 数据流连线 ===
    CLI --> AgentClass
    Web --> AgentClass
    Web --> UI

    AgentClass --> LLMClient
    Stage0 --> DSM
    Stage0 --> UDM

    Stage1 --> P1
    Stage1 --> SysPrompts
    Stage1 --> LLMClient

    Stage2 --> P2
    Stage2 --> DSM
    Stage2 --> LLMClient

    Stage3 --> P3
    Stage3 --> DSM
    Stage3 --> LLMClient
    Stage3 --> RF

    %% === 标注 ===
    style Entry fill:#e3f2fd,stroke:#1565c0
    style Agent fill:#fff3e0,stroke:#e65100
    style LLM fill:#f3e5f5,stroke:#7b1fa2
    style DataLayer fill:#e8f5e9,stroke:#2e7d32
    style UserLayer fill:#fce4ec,stroke:#c62828
    style ReportLayer fill:#fff8e1,stroke:#f9a825
    style Prompts fill:#e0f2f1,stroke:#00695c
    style UI fill:#f5f5f5,stroke:#616161
```

## 数据流说明

```
用户输入行业名称
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Stage 0: 数据采集（纯 Python）                        │
│                                                      │
│ DataSourceManager.gather("AI算力")                    │
│   ├─ 行情: 腾讯 → 新浪 → baostock (主线程)           │
│   ├─ 财务: baostock 季报 (并发)  ←── 7天缓存         │
│   ├─ 公告: 巨潮资讯网 (并发)     ←── 7天缓存         │
│   └─ 新闻: AKShare (并发)         ←── 实时           │
│                                                      │
│ UserDataManager.parse_uploads()                      │
│   └─ 用户上传 .md/.pdf/.docx → 结构化条目            │
│                                                      │
│ → self.context = {market_data, financial_data,       │
│    announcement_data, news_data, user_supplements}   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ Stage 1: 行业全景分析（AI）                           │
│                                                      │
│ 从 context 提取行情摘要 + 财务摘要 + 公告/新闻        │
│ + UserDataManager.summarize_supplements()            │
│ ↓                                                    │
│ 填入 prompts/industry_overview.md                    │
│ ↓                                                    │
│ LLMClient.ask_with_log(system=SYSTEM_PROMPTS[0])    │
│ ↓                                                    │
│ → self.context["industry_overview"]                  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ Stage 2: 公司深度分析（AI）                           │
│                                                      │
│ DataSourceManager.build_company_data()               │
│ └─ 合并行情(PE/市值) + 财务(ROE/毛利率/增速/负债率)  │
│ ↓                                                    │
│ 填入 prompts/company_deep_dive.md                    │
│   + industry_context(Stage 1 输出前3000字)           │
│   + companies(15家全量数据 JSON)                     │
│ ↓                                                    │
│ LLMClient.ask_with_log(system=SYSTEM_PROMPTS[1])    │
│ ↓                                                    │
│ → self.context["company_deep_dive"]                  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│ Stage 3: 投资研判 → 最终报告（AI）                    │
│                                                      │
│ 输入分为两层（防级联幻觉）:                           │
│ ① 原始采集数据: PE/ROE/增速/负债率 统计量            │
│ ② AI分析(仅参考): Stage1 + Stage2 输出               │
│ ↓                                                    │
│ 填入 prompts/investment_thesis.md                    │
│ ↓                                                    │
│ LLMClient.ask_with_log(system=SYSTEM_PROMPTS[2])    │
│ ↓                                                    │
│ ReportFormatter.format_report()                      │
│ ↓                                                    │
│ → demo_output/行业_行业扫描报告_时间戳.md             │
└─────────────────────────────────────────────────────┘
```

## 关键设计决策

| 决策 | 说明 |
|------|------|
| **Stage 0 不调 AI** | 数据采集纯 Python 汇总，避免"AI 传话"导致数据失真 |
| **Stage 3 直出最终报告** | 不再需要单独的"报告格式化 LLM 调用" |
| **原始数据 + AI 分析并列** | Stage 3 同时收到原始 JSON 和 AI 文本，防级联幻觉 |
| **baostock 主线程** | baostock 连接不能跨线程共享 |
| **财务/公告 7 天缓存** | 季报不频繁更新；行情和新闻实时拉取 |
| **多源融合** | 价格 腾讯>新浪>baostock，PE 腾讯实时>baostock日线 |
