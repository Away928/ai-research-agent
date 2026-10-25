"""
集中配置 — 所有可调参数单点管理
=================================

支持环境变量覆盖（优先级：环境变量 > config.py 默认值）。

用法：
    from config import config
    timeout = config.HTTP_TIMEOUT
"""

import os


class _Config:
    """配置容器。实例化一次，全局复用。"""

    # ── 数据源 ──────────────────────────────────────────────

    # 成分股：新浪概念板块 API 返回的 Top N
    MAX_CONSTITUENTS = int(os.environ.get("AGENT_MAX_CONSTITUENTS", "20"))

    # 财务：每行业最多分析的公司数
    MAX_FINANCIAL_COMPANIES = int(os.environ.get("AGENT_MAX_FINANCIAL", "15"))

    # 新闻：取前几家龙头公司的新闻
    TOP_COMPANIES_FOR_NEWS = int(os.environ.get("AGENT_TOP_NEWS_CO", "3"))

    # 新闻：最大返回条数
    NEWS_MAX_ITEMS = int(os.environ.get("AGENT_NEWS_MAX", "20"))

    # 缓存：财务 / 公告有效期（天）
    CACHE_MAX_AGE_DAYS = int(os.environ.get("AGENT_CACHE_DAYS", "7"))

    # HTTP 请求统一超时（秒）
    HTTP_TIMEOUT = int(os.environ.get("AGENT_HTTP_TIMEOUT", "10"))

    # 公告：取前几家龙头的公告
    ANNOUNCEMENT_TOP_COMPANIES = int(
        os.environ.get("AGENT_ANNOUNCEMENT_TOP_CO", "10"))
    ANNOUNCEMENT_MAX_ITEMS = int(
        os.environ.get("AGENT_ANNOUNCEMENT_MAX", "30"))

    # 各阶段 max_tokens + 重试次数
    STAGE_MAX_TOKENS = {
        "industry_overview": int(
            os.environ.get("AGENT_TOKENS_OVERVIEW", "3072")),
        "company_deep_dive": int(
            os.environ.get("AGENT_TOKENS_DEEP_DIVE", "4096")),
        "investment_thesis": int(
            os.environ.get("AGENT_TOKENS_THESIS", "8192")),
    }

    RETRY_COUNT = int(os.environ.get("AGENT_RETRY_COUNT", "2"))

    # LLM 推理参数
    TEMPERATURE = float(os.environ.get("AGENT_TEMPERATURE", "0.3"))

    # Token 安全：压缩时的保守上下文上限
    FALLBACK_CONTEXT_LIMIT = int(
        os.environ.get("AGENT_CTX_LIMIT", "50000"))

    # ── LLM 默认值 ──────────────────────────────────────────

    ANTHROPIC_API_URL = os.environ.get(
        "ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages")
    ANTHROPIC_VERSION = "2023-06-01"

    DEFAULT_ANTHROPIC_MODEL = os.environ.get(
        "ANTHROPIC_MODEL", "claude-sonnet-4-6")
    DEFAULT_OPENAI_COMPAT_MODEL = os.environ.get(
        "OPENAI_MODEL", "deepseek-chat")

    DEFAULT_OPENAI_BASE_URL = os.environ.get(
        "OPENAI_BASE_URL", "https://api.openai.com/v1")


# 全局单例
config = _Config()
