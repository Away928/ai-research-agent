# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI Research Agent — 给定行业名称，自动完成四阶段投资研究工作流：数据采集 → 行业全景 → 公司深度 → 投资研判。Streamlit Web 界面 + CLI。

## 代码规范

- 优先选择编辑而非重写整个文件
- 一个文件不超过 400 行，超了就拆
- 嵌套不超过 4 层

## 项目结构

- `app.py` — Streamlit Web 界面入口
- `cli.py` — 命令行入口
- `agent_workflow.py` — 4 阶段工作流编排（核心）
- `agent_helpers.py` — AI 调用编排（重试/校验/上下文压缩）
- `llm_client.py` — 多模型 LLM 客户端（Anthropic + OpenAI 兼容）
- `config.py` — 集中配置单例，支持环境变量覆盖
- `prompts/` — Prompt 模板（.md）+ 系统角色（system_prompts.py）+ 输出校验（validators.py）
- `ui/` — Streamlit UI 组件（侧边栏/输入区/数据卡片/图表/样式）
- `tools/data_sources/` — 数据源（行情/财务/公告/新闻），DataSourceManager 统一入口
- `tools/report_formatter.py` — 报告格式化
- `tools/user_data.py` — 用户上传文件解析
- `utils/token_counter.py` — tiktoken 计数 + 上下文压缩
- `tests/` — 单元测试（111 个用例，零 mock）

## 数据流

1. `DataSourceManager.gather(industry)` → 行情（腾讯+新浪+baostock）、财务（baostock）、公告（巨潮）、新闻（AKShare）
2. `AIResearchAgentV2` 按 stage_1→2→3→4 顺序执行，每阶段将输出写入 `self.context`
3. Stage 4 生成最终报告，保存到 `demo_output/`

## 多模型后端

- `llm_client.py` 支持 Anthropic 原生 API 和 OpenAI 兼容 API
- 通过环境变量自动检测后端类型
- 无 API key 时自动降级为 Prompt 模板输出模式

## 测试

```bash
python -m pytest tests/ -v
```
