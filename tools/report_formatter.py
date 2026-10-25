"""
报告格式化工具
===============

将AI生成的原始分析内容格式化为结构化的Markdown研究报告。
同时生成工作流日志的统计摘要。
"""

import re
from datetime import datetime
from typing import List, Dict
from tools.claim_audit import audit_financial_markers


class ReportFormatter:

    def __init__(self):
        self.disclaimer = (
            "> ⚠️ **重要声明：** 本报告由AI辅助生成（AI Research Agent），"
            "仅用于展示AI在投资研究中的辅助能力。报告中包含的数据、分析和结论"
            "**不构成任何投资建议**。使用者应独立验证所有关键信息，并自行承担"
            "投资决策的风险。\n"
        )

    def format_report(
        self,
        raw_content: str,
        industry: str,
        work_log: List[Dict],
        context: Dict = None,
    ) -> str:
        """
        将AI原始输出格式化为完整的研究报告。

        Args:
            raw_content: AI生成的原始内容
            industry: 行业名称
            work_log: 工作流各阶段的日志
            context: agent 的 context 字典（含数据源状态等元信息）
        """
        header = self._build_header(industry, work_log, context)
        footer = self._build_footer(work_log, context, raw_content)

        content = self._clean_content(raw_content)

        return f"{header}\n\n{content}\n\n{footer}"

    def _build_header(
        self, industry: str, work_log: List[Dict], context: Dict = None
    ) -> str:
        """构建报告头部元信息。"""
        total_duration = sum(s["duration_seconds"] for s in work_log)
        ai_duration = total_duration  # AI处理时间（扣除数据采集的等待时间可以用更精确的）

        # 数据源状态摘要
        source_status = ""
        if context:
            raw = context.get("raw_data", {})
            status = raw.get("数据源状态", {})
            labels = {
                "market_data": "行情",
                "financial_data": "财务",
                "announcement_data": "公告",
                "news_data": "新闻",
            }
            source_lines = [
                f"| {labels[k]} | {v.split()[0] if '✅' in v else '不可用'} |"
                for k, v in status.items() if k in labels
            ]
            if source_lines:
                source_status = (
                    "\n### 数据源状态\n\n"
                    "| 数据维度 | 状态 |\n"
                    "|---------|------|\n"
                    + "\n".join(source_lines)
                    + "\n"
                )

        if (context or {}).get("demo_mode"):
            header = f"""# 🧪 {industry}｜Research Agent 离线产品演示报告

> **纯合成示例 / 非真实投资研究 / 非 AI 模型生成**
> 本报告使用项目内固定虚构数据和预先编写的研究情景。
> 未连接行情或财务接口，未调用大模型，所有数字均不得视为市场事实。

**演示生成日期：** {datetime.now().strftime('%Y-%m-%d')}
**合成数据快照日期：** {(context.get('raw_data') or {}).get('采集时间', '未注明')}
**体验方式：** 无 API Key、无网络、无付费模型
**展示的工作流阶段：** {len(work_log)} 个（预设演示，不代表真实执行）

{source_status}

---
"""
        else:
            header = f"""# 🏭 {industry}行业投资研究扫描报告

**生成日期：** {datetime.now().strftime('%Y-%m-%d')}
**研究方式：** AI辅助研究（AI Research Agent）
**工作流耗时：** {total_duration:.1f}秒（含数据采集和 AI 推理）
**研究阶段：** {len(work_log)} 个阶段

{source_status}
{self.disclaimer}

---
"""
        return header

    def _build_footer(
        self, work_log: List[Dict], context: Dict = None,
        raw_content: str = "",
    ) -> str:
        """构建报告底部的工作流统计和附录。"""
        total_duration = sum(s["duration_seconds"] for s in work_log)

        stage_details = ""
        for i, stage in enumerate(work_log, 1):
            pct = (
                (stage["duration_seconds"] / total_duration * 100)
                if total_duration > 0
                else 0
            )
            stage_details += (
                f"| {i} | {stage['stage']} | "
                f"{stage['duration_seconds']:.1f}s ({pct:.1f}%) | "
                f"{stage['notes']} |\n"
            )

        evidence_section = self._financial_evidence(context)
        sources_table = self._source_overview(context)
        audit_heading = "E" if evidence_section else "D"
        audit_section = self._financial_marker_review(raw_content, context, audit_heading)
        author_heading = "### F. 作者" if evidence_section else "### E. 作者"

        demo_mode = bool((context or {}).get("demo_mode"))
        author_details = (
            "**Research Agent Demo** — 纯合成示例，未包含用户资料或个人联系方式。"
            if demo_mode else
            "**Research Agent** — 开源研究项目（使用者应自行核验生成内容）"
        )
        flow_description = (
            "以下为四阶段**预设展示路径**，没有运行实时采集、AI 推理或投资研究。"
            if demo_mode else
            "本报告由 AI Research Agent 按以下四阶段工作流自动编排生成。"
        )
        disclosure = (
            "- 本次展示来自完全虚构的固定测试包，正文为预设文本；没有调用任何模型。\n"
            "- 数据和公司均为合成演示材料，不构成真实证券事实或投资建议。\n"
            "- FIN 引用只对照合成快照内的数字，不代表外部事实核验。"
            if demo_mode else
            "- 本报告中由AI生成的内容已标注，核心分析框架和 prompt 由人工设计\n"
            "- 财务与市场数据需通过官方披露或其他独立可信渠道复核\n"
            "- AI 生成的投资建议仅作为研究参考，最终决策需人工判断\n"
            "- AI 在不确定时倾向于编造而非承认不知道——请对所有AI判断持审慎态度"
        )
        footer = f"""---

## 📎 附录

### A. 研究流程说明

{flow_description}

| # | 阶段 | 耗时 | 说明 |
|---|------|------|------|
{stage_details}

### B. AI使用声明

{disclosure}

### C. 本次采集来源（非事实核验）

{sources_table}

{evidence_section}
{audit_section}
{author_heading}

{author_details}

---
*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return footer

    @staticmethod
    def _financial_marker_review(content: str, context: Dict = None,
                                 heading: str = "E") -> str:
        """Describe only annotated number-to-record agreement, never factual truth."""
        raw = (context or {}).get("raw_data") or {}
        reviewed = audit_financial_markers(content, raw)
        title = f"### {heading}. 财务数字引用记录对账（非事实核验)"
        caveat = (
            "本检查仅对正文中形如 `[[FIN-000001-roe_pct=8.0]]` 的显式标记，"
            "核对本次采集数据中股票代码、指标及标记数值是否一致。"
            "不检查未标记数字、标记附近的文字陈述、数据提供方的真实性或投资结论。"
        )
        if not reviewed:
            return f"{title}\n\n{caveat}\n\n未发现可机读的财务引用标记；不能视为检查通过。\n"
        good = sum(r["status"] == "record_value_match" for r in reviewed)
        flagged = [r for r in reviewed if r["status"] != "record_value_match"]
        if not flagged:
            result = "本次全部标记数值与采集快照一致，但不代表正文获得事实认证。"
        else:
            rows = [
                f"| {r['marker'].replace('|', '｜')} | {r['status']} | "
                f"{str(r.get('source_value')).replace('|', '｜')} |"
                for r in flagged
            ]
            result = (
                "存在需要人工复核的标记：\n\n"
                "| 标记 | 检查状态 | 采集值 |\n|---|---|---|\n"
                + "\n".join(rows)
            )
        return (
            f"{title}\n\n{caveat}\n\n"
            f"可机读标记共 {len(reviewed)} 条；采集数值匹配 {good} 条，"
            f"需复核 {len(flagged)} 条。\n\n{result}\n"
        )

    @staticmethod
    def _source_overview(context: Dict = None) -> str:
        """Use only collected source labels; never guess providers or freshness."""
        raw = (context or {}).get("raw_data") or {}
        categories = (
            ("market_data", "行情"),
            ("financial_data", "财务"),
            ("announcement_data", "公告"),
            ("news_data", "新闻"),
        )

        def safe(value):
            if not isinstance(value, str) or not value.strip():
                return "未提供"
            return value.replace("|", "｜").replace("\r", " ").replace("\n", " ").strip()

        rows = []
        for key, title in categories:
            data = raw.get(key)
            if not isinstance(data, dict) or not data:
                rows.append(f"| {title} | 无可用数据 | 未提供 | 未核验 |")
                continue
            label = safe(data.get("source"))
            fetched = safe(data.get("fetch_timestamp"))
            rows.append(f"| {title} | {label} | {fetched} | 未核验 |")
        return (
            "来源标签仅为采集程序的元信息，不保证数据提供方、观测日期或真实性。"
            "获取时间不等于金融数据所属日期；缺少具体日期时应保持未知。\n\n"
            "| 数据类型 | 实际来源标签 | 获取时间 | 事实核验 |\n"
            "|---|---|---|---|\n" + "\n".join(rows)
        )

    @staticmethod
    def _financial_evidence(context: Dict = None) -> str:
        """Deterministic snapshot of collected figures, not claim verification."""
        raw = (context or {}).get("raw_data") or {}
        fin = raw.get("financial_data") or {}
        companies = fin.get("公司财务") or []
        metrics = (
            ("roe_pct", "ROE(%)"),
            ("gross_margin_pct", "毛利率(%)"),
            ("revenue_growth_pct", "营收增速(%)"),
            ("net_profit_growth_pct", "净利增速(%)"),
            ("debt_ratio_pct", "负债率(%)"),
        )
        rows = []
        def cell(v):
            return str(v if v is not None else "未知").replace("|", "｜").replace("\n", " ")
        for company in companies:
            if not isinstance(company, dict):
                continue
            code = company.get("code", "")
            if not code:
                continue
            periods = company.get("_metric_periods") or {}
            publication = company.get("_metric_publication_dates") or {}
            methods = company.get("_metric_methods") or {}
            for field, label in metrics:
                value = company.get(field)
                if value is None:
                    continue
                rows.append(
                    f"| `FIN-{cell(code)}-{field}` | {cell(code)} | "
                    f"{cell(company.get('name'))} | {label} | {cell(value)} | "
                    f"{cell(periods.get(field))} | {cell(company.get('_source'))} | "
                    f"{cell(publication.get(field))} | {cell(methods.get(field))} |"
                )
        if not rows:
            return ""
        return (
            "### D. 采集财务数字对照（非事实核验）\n\n"
            "以下 ID 仅指向本次采集的数据记录，不能证明供应商数字正确，"
            "也不代表 AI 正文已逐项完成证据比对。报告期未知时不得以采集时间代替。\n\n"
            "| 记录 ID | 股票代码 | 公司 | 指标 | 数值（%） | 报告期 | 采集来源标签 | 披露日期 | API字段或推导口径 |\n"
            "|---|---|---|---|---:|---|---|---|---|\n"
            + "\n".join(rows) + "\n"
        )

    def _clean_content(self, raw: str) -> str:
        """清理AI原始输出中的格式问题。"""
        # 去除多余的空白行
        content = re.sub(r'\n{4,}', '\n\n\n', raw)
        # 确保标题前有空行
        content = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', content)
        return content.strip()

    def generate_workflow_summary(self, work_log: List[Dict]) -> str:
        """生成工作流效率摘要（供方法论报告使用）。"""
        total = sum(s["duration_seconds"] for s in work_log)

        summary = "## 工作流效率摘要\n\n"
        summary += f"- **总耗时：** {total:.1f}秒（约{total/60:.1f}分钟）\n"
        summary += f"- **AI处理阶段：** {len(work_log)}个\n\n"

        summary += "### 各阶段耗时分布\n\n"
        for stage in work_log:
            bar_len = (
                int(stage["duration_seconds"] / total * 40) if total > 0 else 0
            )
            bar = "█" * bar_len
            summary += (
                f"`{stage['stage']:30s}` {bar} {stage['duration_seconds']:.1f}s\n"
            )

        summary += "\n### 效率洞察\n\n"
        summary += "- 数据采集阶段最耗时（依赖 baostock/新浪等在线API响应速度）\n"
        summary += "- AI推理阶段速度远快于人工同等分析\n"
        summary += "- 瓶颈在数据采集 I/O，而非分析本身\n"

        return summary


if __name__ == "__main__":
    # 测试
    formatter = ReportFormatter()
    sample_log = [
        {"stage": "data_collection", "duration_seconds": 45.2, "notes": "数据采集"},
        {"stage": "industry_overview", "duration_seconds": 32.1, "notes": "行业全景"},
    ]
    print(formatter.generate_workflow_summary(sample_log))
