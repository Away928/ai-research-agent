# 🧠 AI Research Agent

**输入行业名称，AI 自动完成数据采集、多维度分析和报告撰写，你只需做最终判断。**

[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.4-blue)]()
[![Streamlit Cloud](https://img.shields.io/badge/🚀-在线体验-red)](https://ai-research-agent.streamlit.app)

```
📊 数据采集 → 🔍 行业全景 → 🏢 公司深度 → 📝 投资研判
```

## ✨ 核心特性

### 🔬 五维数据采集（全部免费，无需付费终端）

| 维度 | 数据源 | 说明 |
|------|------|------|
| **行情** | 腾讯财经 + 新浪财经 + baostock | 逐字段优选，实时拉取 |
| **财务** | baostock 日线财报 | ROE / 毛利率 / 营收增速 / 净利增速 / 负债率 |
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

成分股通过新浪概念板块 API 实时获取，按流通市值排序，动态反映市场变化。

### 🖥️ Streamlit Web 界面

Terminal Blue 专业深蓝风格，Pipeline 时间轴可视化（实时耗时），历史研究记录，数据卡片 + 交互图表。每阶段报告在网页中直接可读。

### 🔄 智能降级 + 质量保障

- **有 API key** → 四阶段 AI 全自动完成
- **无 API key** → Python 数据采集正常运行 + 打印 Prompt 模板供手动使用
- **上下文安全** → tiktoken 自动计数，超出上限智能压缩
- **输出校验** → AI 输出后检查数字引用、来源标注、章节完整性，缺失自动追问补全

---

## 🚀 快速开始

### 🌐 在线使用（推荐）

👉 **[ai-research-agent.streamlit.app](https://ai-research-agent.streamlit.app)**

浏览器打开即用，无需安装任何东西。在侧边栏配置 API key，选择行业即可开始分析。

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

是的。成分股通过新浪概念板块 API 实时获取，按流通市值排序，不使用硬编码数据。

</details>

<details>
<summary><b>支持哪些行业？</b></summary>

当前支持 15 个行业，与新浪热门概念板块一一映射。在 `market_sources.py` 的 `_SINA_CONCEPT_NODE_MAP` 中加入新的行业名 → 概念板块 Node ID 即可扩展。

</details>

<details>
<summary><b>财务数据为什么有些公司缺失？</b></summary>

财务数据来自 baostock 日线财报（T+1），依赖 A 股季报披露进度。某家公司指标为空可能是该季度财报尚未披露，系统会向前追溯最多 3 年，并标注数据期间供参考。

</details>

---

## ⚠️ 局限性

- 研报暂无免费在线源，公告和新闻可作为部分替代
- AI 在不确定时倾向于编造而非承认不知道 — 所有分析需人工验证
- 仅基于公开信息，无法获取一手调研数据
- 报告中包含的投资分析**不构成投资建议**

---

## 👤 作者

**William Lu** — 香港中文大学（深圳）金融专业 2028 届

- GitHub：[Away928/ai-research-agent](https://github.com/Away928/ai-research-agent)
- 📧 luyuwei928@163.com

---

MIT License
