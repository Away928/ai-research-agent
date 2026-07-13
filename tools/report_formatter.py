"""
报告格式化工具
===============

将AI生成的原始分析内容格式化为结构化的Markdown研究报告。
同时生成工作流日志的统计摘要。
"""

import re
from datetime import datetime
from typing import List, Dict


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
        footer = self._build_footer(work_log, context)

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
                f"| {labels.get(k, k)} | {v.split()[0] if '✅' in v else '不可用'} |"
                for k, v in status.items()
            ]
            if source_lines:
                source_status = (
                    "\n### 数据源状态\n\n"
                    "| 数据维度 | 状态 |\n"
                    "|---------|------|\n"
                    + "\n".join(source_lines)
                    + "\n"
                )

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
        self, work_log: List[Dict], context: Dict = None
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

        footer = f"""---

## 📎 附录

### A. 研究流程说明

本报告由 AI Research Agent 按以下四阶段工作流自动编排生成：

| # | 阶段 | 耗时 | 说明 |
|---|------|------|------|
{stage_details}

### B. AI使用声明

- 本报告中由AI生成的内容已标注，核心分析框架和 prompt 由人工设计
- 所有财务/市场数据需在使用前通过 Wind 等专业终端验证
- AI 生成的投资建议仅作为研究参考，最终决策需人工判断
- AI 在不确定时倾向于编造而非承认不知道——请对所有AI判断持审慎态度

### C. 数据来源

| 数据类型 | 来源 | 说明 |
|---------|------|------|
| 个股行情（价格/PE/市值/涨跌幅） | 腾讯财经 qt.gtimg.cn + 新浪财经 hq.sinajs.cn + baostock | 逐字段择优，精度最高 |
| 行业指数行情 | 新浪指数 sz399363（国证算力） + 成分股汇总推导 | 独立获取 |
| 财务数据（ROE/毛利率/营收增速/净利增速/负债率） | baostock 日线财报 | T+1 更新，非实时 |
| 公告 | 巨潮资讯网 cninfo.com.cn | 真实公告标题+PDF链接 |
| 新闻 | 公开财经媒体（通过 AKShare 聚合） | 龙头公司相关新闻 |

### D. 作者

**William Lu** — 香港中文大学（深圳）金融专业
- 项目地址：[Away928/ai-research-agent](https://github.com/Away928/ai-research-agent)
- 联系方式：luyuwei928@163.com

---
*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return footer

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
