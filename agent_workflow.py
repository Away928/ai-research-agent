"""
AI Research Agent — 4阶段投研工作流编排。
用法见 cli.py 或 README.md。William Lu
"""

import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent
PROMPTS_DIR = ROOT / "prompts"
TOOLS_DIR = ROOT / "tools"
OUTPUT_DIR = ROOT / "demo_output"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS_DIR))

from llm_client import LLMClient
from tools.data_sources import DataSourceManager
from tools.report_formatter import ReportFormatter
from tools.user_data import UserDataManager
from agent_helpers import (
    STAGE_CONFIG,
    call_ai_or_fallback,
    compress_context_for_prompt,
    validate_and_chase,
)


class AIResearchAgentV2:
    """AI投研Agent v2 — 4阶段工作流 + 智能降级架构。"""

    def __init__(
        self,
        industry: str,
        api_key: str = "",
        model: str = "",
        model_backend: str = "",
        base_url: str = "",
        uploads: list = None,
    ):
        self.industry = industry
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.work_log = []
        self.context = {}
        self.data_manager = DataSourceManager()
        self.formatter = ReportFormatter()

        self.llm = LLMClient(
            model_backend=model_backend, api_key=api_key,
            base_url=base_url, model=model,
        )
        self.ai_mode = self.llm.is_available
        self._upload_files = uploads or []

        if self.ai_mode:
            backend_label = (
                "Anthropic" if self.llm.model_backend == "anthropic"
                else "OpenAI兼容"
            )
            print(f"🤖 AI 自动模式已启用（{backend_label}: {self.llm.model}）")
        else:
            print("📋 降级模式：Python 数据采集 + Prompt 模板输出")

    def log(self, stage: str, duration: float, output: str, notes: str = ""):
        self.work_log.append({
            "stage": stage, "duration_seconds": round(duration, 1),
            "output_length": len(output),
            "ai_generated": self.ai_mode and len(output) > 100,
            "notes": notes,
        })

    def _load_prompt(self, name: str) -> str:
        path = PROMPTS_DIR / f"{name}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return f"请分析 {self.industry} 行业。"

    # ═════════════════════════════════════════════════════════
    # Stage 1 — 数据采集（纯 Python）
    # ═════════════════════════════════════════════════════════

    def stage_context_gathering(self) -> str:
        """采集四维数据包 + 用户上传文件。纯 Python，不调用 AI。"""
        print(f"\n{'='*60}")
        print(f"📊 阶段1/4: 数据采集 — 【{self.industry}】")
        print(f"{'='*60}")

        t0 = time.time()
        raw_data = self.data_manager.gather(self.industry)

        user_mgr = UserDataManager()
        llm_for_summary = self.llm if self.ai_mode else None
        supplements = user_mgr.parse_uploads(
            self._upload_files, llm_client=llm_for_summary,
        )
        raw_data["user_supplements"] = supplements
        raw_data["数据源状态"]["user_supplements"] = (
            f"✅ {len(supplements)}条" if supplements
            else "— 无用户补充数据"
        )
        self.data_manager.print_summary(raw_data)
        self.context["raw_data"] = raw_data
        self.context["market_data"] = raw_data.get("market_data", {})
        self.context["financial_data"] = raw_data.get("financial_data", {})
        self.context["announcement_data"] = raw_data.get("announcement_data", {})
        self.context["news_data"] = raw_data.get("news_data", {})
        self.context["user_supplements"] = raw_data.get("user_supplements", {})

        status_lines = [
            f"{label}: {raw_data.get('数据源状态', {}).get(key, '?')}"
            for key, label in [
                ("market_data", "行情"), ("financial_data", "财务"),
                ("announcement_data", "公告"), ("news_data", "新闻"),
            ]
        ]
        print(f"  📊 数据源状态 — {' | '.join(status_lines)}")

        duration = time.time() - t0
        module_count = sum(
            1 for k in raw_data
            if k not in ("行业", "采集时间", "数据源状态") and raw_data.get(k)
        )
        self.log("data_collection", duration, "",
                 f"四维数据采集完成，{module_count}个数据模块")
        return ""

    # ═════════════════════════════════════════════════════════
    # Stage 2 — 行业全景分析
    # ═════════════════════════════════════════════════════════

    def stage_industry_overview(self) -> str:
        """行业定义/空间/生命周期/供需/政策/技术。"""
        print(f"\n{'='*60}")
        print(f"🔍 阶段2/4: 行业全景分析")
        print(f"{'='*60}")

        t0 = time.time()
        cfg = STAGE_CONFIG["industry_overview"]
        mkt = self.context.get("market_data", {})
        nws = self.context.get("news_data", {})
        ann = self.context.get("announcement_data", {})
        fin = self.context.get("financial_data", {})

        data = {
            "行业": self.industry,
            "行情摘要": {
                "成分股数量": len(mkt.get('成分股', [])),
                "PE中位数": mkt.get('行情', {}).get('pe_median', 'N/A'),
                "总市值(亿)": mkt.get('行情', {}).get('market_cap_total', 'N/A'),
                "指数名称": mkt.get('行情', {}).get('index_name', ''),
                "指数涨跌幅": mkt.get('行情', {}).get('index_change_pct', ''),
            },
            "财务摘要": {
                "公司数量": len(fin.get('公司财务', [])),
                "前8家": [
                    {"名称": c.get('name'), "ROE(%)": c.get('roe_pct'),
                     "毛利率(%)": c.get('gross_margin_pct'),
                     "营收增速(%)": c.get('revenue_growth_pct'),
                     "净利增速(%)": c.get('net_profit_growth_pct'),
                     "负债率(%)": c.get('debt_ratio_pct')}
                    for c in (fin.get('公司财务', []) or [])[:8]
                ],
                "指标说明": fin.get('指标说明', []),
            },
            "公告摘要": [
                {"日期": a.get('date', ''), "公司": a.get('company', ''),
                 "类型": a.get('type', ''), "标题": a.get('title', '')}
                for a in (ann.get('公告', []) or [])[:8]
            ],
            "近期新闻": [
                {"标题": n.get('title', ''), "日期": n.get('date', ''),
                 "来源": n.get('source', ''),
                 "摘要": (n.get('summary', '') or '')[:200]}
                for n in (nws.get('新闻', []) or [])[:8]
            ],
            "用户补充数据": UserDataManager.summarize_supplements(
                self.context.get("user_supplements", {})),
            "数据来源": "腾讯行情+baostock财报+巨潮公告+财经新闻",
            "_metadata": {
                "数据时效": (
                    "行情数据为实时采集（秒级延迟）；"
                    "财务数据来自 baostock 日线财报（T+1，依赖季报披露进度，"
                    "当前可能有部分公司最新季报尚未入库）；"
                    "公告为近 3 个月内公开信息；"
                    "新闻为近 1 周内公开财经媒体报道"
                ),
                "注意": (
                    "如果某家公司的财务指标为空，不代表数据缺失，"
                    "可能只是该季度财报尚未被数据源收录。"
                    "分析时应基于有数据的公司得出结论，"
                    "并标注'基于 N 家已披露财报的公司'。"
                ),
                "采集时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

        prompt = self._load_prompt("industry_overview")
        prompt = prompt.replace("{{INDUSTRY}}", self.industry)
        prompt = prompt.replace("{{DATA}}",
                                json.dumps(data, ensure_ascii=False, indent=2))

        ai_output = call_ai_or_fallback(
            self, "industry_overview", prompt, "行业全景",
            max_tokens=cfg["max_tokens"], retry_count=cfg["retry_count"],
        )
        ai_output = validate_and_chase(
            self, "industry_overview", ai_output, cfg["max_tokens"])
        self.context["industry_overview"] = ai_output

        duration = time.time() - t0
        self.log("industry_overview", duration, ai_output, "行业全景分析")
        return ai_output

    # ═════════════════════════════════════════════════════════
    # Stage 3 — 公司深度分析
    # ═════════════════════════════════════════════════════════

    def stage_company_deep_dive(self) -> str:
        """集中度/头部对比/盈利/财务健康/估值/竞争壁垒/预警。"""
        print(f"\n{'='*60}")
        print(f"🏢 阶段3/4: 公司深度分析")
        print(f"{'='*60}")

        t0 = time.time()
        cfg = STAGE_CONFIG["company_deep_dive"]
        companies = DataSourceManager.build_company_data(
            self.context.get("market_data", {}),
            self.context.get("financial_data", {}),
        )
        industry_context = self.context.get("industry_overview", "")

        # Token 安全：分配剩余空间给历史分析输出
        try:
            from utils.token_counter import count_tokens, safe_context_size
            prompt_base = (
                self._load_prompt("company_deep_dive")
                + self.industry
                + json.dumps(companies, ensure_ascii=False)
                + json.dumps(
                    UserDataManager.summarize_supplements(
                        self.context.get("user_supplements", {})),
                    ensure_ascii=False, indent=2)
            )
            remaining = max(
                safe_context_size(self.llm.model)
                - count_tokens(prompt_base), 500
            )
        except Exception:
            remaining = 2000  # conservative default
        from utils.token_counter import compress_if_needed
        industry_context = compress_if_needed(
            industry_context, remaining, "行业全景")

        prompt = self._load_prompt("company_deep_dive")
        prompt = prompt.replace("{{INDUSTRY}}", self.industry)
        prompt = prompt.replace("{{INDUSTRY_CONTEXT}}", industry_context)
        prompt = prompt.replace("{{COMPANIES}}",
                                json.dumps(companies, ensure_ascii=False, indent=2))
        prompt = prompt.replace(
            "{{USER_SUPPLEMENTS}}",
            json.dumps(
                UserDataManager.summarize_supplements(
                    self.context.get("user_supplements", {})),
                ensure_ascii=False, indent=2))

        ai_output = call_ai_or_fallback(
            self, "company_deep_dive", prompt, "公司深度",
            max_tokens=cfg["max_tokens"], retry_count=cfg["retry_count"],
        )
        ai_output = validate_and_chase(
            self, "company_deep_dive", ai_output, cfg["max_tokens"])
        self.context["company_deep_dive"] = ai_output

        duration = time.time() - t0
        self.log("company_deep_dive", duration, ai_output,
                 f"分析{len(companies)}家公司（竞争+财务+估值）")
        return ai_output

    # ═════════════════════════════════════════════════════════
    # Stage 4 — 投资研判与报告生成
    # ═════════════════════════════════════════════════════════

    def stage_investment_thesis(self) -> str:
        """周期/信号/风险/龙头对比/Red Team → 最终报告。"""
        print(f"\n{'='*60}")
        print(f"📝 阶段4/4: 投资研判与报告生成")
        print(f"{'='*60}")

        t0 = time.time()
        cfg = STAGE_CONFIG["investment_thesis"]
        mkt = self.context.get("market_data", {})
        nws = self.context.get("news_data", {})

        companies = DataSourceManager.build_company_data(
            self.context.get("market_data", {}),
            self.context.get("financial_data", {}),
        )
        valid_roe = [c["ROE(%)"] for c in companies if c["ROE(%)"] is not None]
        valid_growth = [c["营收增速(%)"] for c in companies if c["营收增速(%)"] is not None]
        valid_debt = [c["负债率(%)"] for c in companies if c["负债率(%)"] is not None]
        valid_pe = [c["PE"] for c in companies if c.get("PE") is not None and c["PE"] > 0]

        raw_stats = {
            "PE中位数": mkt.get('行情', {}).get('pe_median'),
            "PE范围": (round(min(valid_pe), 1), round(max(valid_pe), 1)) if valid_pe else None,
            "总市值(亿)": mkt.get('行情', {}).get('market_cap_total'),
            "成分股数量": len(valid_pe),
            "行业平均ROE(%)": round(statistics.mean(valid_roe), 1) if valid_roe else None,
            "营收增速中位数(%)": round(statistics.median(valid_growth), 1) if valid_growth else None,
            "负债率均值(%)": round(statistics.mean(valid_debt), 1) if valid_debt else None,
            "近期新闻": [n.get('title', '') for n in (nws.get('新闻', []) or [])[:5]],
            "用户补充数据": UserDataManager.summarize_supplements(
                self.context.get("user_supplements", {})),
        }

        overview, deep_dive = compress_context_for_prompt(
            self.llm.model,
            self.context.get("industry_overview", ""),
            self.context.get("company_deep_dive", ""),
        )

        base_prompt = (
            self._load_prompt("investment_thesis")
            .replace("{{INDUSTRY}}", self.industry)
            .replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
        )
        prompt = base_prompt.replace(
            "{{CONTEXT}}",
            json.dumps({
                "行业": self.industry,
                "原始采集数据": raw_stats,
                "AI分析_行业全景": overview,
                "AI分析_公司深度": deep_dive,
            }, ensure_ascii=False, indent=2),
        )

        ai_output = call_ai_or_fallback(
            self, "investment_thesis", prompt, "投资研判",
            max_tokens=cfg["max_tokens"], retry_count=cfg["retry_count"],
        )
        ai_output = validate_and_chase(
            self, "investment_thesis", ai_output, cfg["max_tokens"])
        self.context["final_report"] = ai_output

        # 格式化并保存
        formatted = self.formatter.format_report(
            ai_output, self.industry, self.work_log, self.context)
        self.context["formatted_report"] = formatted

        safe_name = self.industry.replace("/", "-").replace(" ", "_")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{safe_name}_行业扫描报告_{self.session_id}.md"
        output_path.write_text(formatted, encoding="utf-8")
        print(f"  📄 报告已保存: {output_path}")

        duration = time.time() - t0
        self.log("investment_thesis", duration, ai_output,
                 f"报告 → {output_path.name}")
        return ai_output

    # ═════════════════════════════════════════════════════════
    # 工作流编排
    # ═════════════════════════════════════════════════════════

    def run(self) -> dict:
        """执行完整 4 阶段工作流。"""
        print(f"\n{'#'*60}")
        print(f"# AI Research Agent v2 启动")
        print(f"# 行业: {self.industry}")
        print(f"# 模式: {'🤖 AI 自动' if self.ai_mode else '📋 降级'}")
        print(f"# 会话: {self.session_id}")
        print(f"{'#'*60}")

        workflow_start = time.time()
        stages = [
            ("data_collection", self.stage_context_gathering),
            ("industry_overview", self.stage_industry_overview),
            ("company_deep_dive", self.stage_company_deep_dive),
            ("investment_thesis", self.stage_investment_thesis),
        ]
        for name, func in stages:
            try:
                func()
            except Exception as e:
                print(f"\n⚠️  阶段 [{name}] 出错: {e}")
                self.context[f"{name}_error"] = str(e)

        total_duration = time.time() - workflow_start
        log_path = OUTPUT_DIR / f"work_log_{self.session_id}.json"
        log_summary = {
            "industry": self.industry,
            "session_id": self.session_id,
            "ai_mode": self.ai_mode,
            "total_duration_seconds": round(total_duration, 1),
            "stages": self.work_log,
        }
        log_path.write_text(
            json.dumps(log_summary, ensure_ascii=False, indent=2),
            encoding="utf-8")

        # ── 写入历史索引 ──
        _append_history(self, total_duration)

        print(f"\n{'='*60}")
        print(f"✅ 工作流完成  总耗时: {total_duration:.1f}s")
        print(f"   模式: {'AI 自动' if self.ai_mode else '降级'}")
        print(f"   日志: {log_path}")
        print(f"{'='*60}")
        return log_summary


if __name__ == "__main__":
    from cli import main
    main()


# ── 历史索引 ────────────────────────────────────────────────

_HISTORY_FILE = OUTPUT_DIR / "_history.json"


def _append_history(agent, total_duration: float):
    """追加一条研究记录到历史索引文件。"""
    raw = agent.context.get("raw_data", {})
    status = raw.get("数据源状态", {}) if raw else {}
    final = agent.context.get("final_report", "")
    preview = final[:200] if final else ""

    safe_name = agent.industry.replace("/", "-").replace(" ", "_")
    record = {
        "session_id": agent.session_id,
        "industry": agent.industry,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration_s": round(total_duration, 1),
        "mode": "AI 自动" if agent.ai_mode else "降级",
        "report_file": f"{safe_name}_行业扫描报告_{agent.session_id}.md",
        "data_sources": {
            "行情": status.get("market_data", "?"),
            "财务": status.get("financial_data", "?"),
            "公告": status.get("announcement_data", "?"),
            "新闻": status.get("news_data", "?"),
        },
        "preview": preview,
    }

    history = []
    if _HISTORY_FILE.exists():
        try:
            history = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            history = []
    # 去重
    history = [h for h in history if h.get("session_id") != record["session_id"]]
    history.append(record)
    history = history[-50:]  # 只保留最近 50 条
    _HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8")
