"""Tests for prompts/validators.py — quality-based validation, zero mocking."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from prompts.validators import (
    validate_stage_output,
    build_chase_prompt,
    merge_chase_output,
)


class TestValidateStageOutput:
    """validate_stage_output — quality-based section completeness check."""

    # ── industry_overview ───────────────────────────────────

    def test_all_sections_present_returns_empty(self):
        output = """
        ## 行业定义
        算力行业是指提供计算基础设施的产业链。
        上游包括芯片设计和制造（海光信息 毛利率 65%，中科曙光 PE 35），
        中游包括服务器组装和IDC运营（毛利率 25%-40%），
        下游包括云计算和AI应用服务。

        据 baostock 财报数据，行业平均 ROE 为 8.5%，营收增速中位数为 12.3%。
        目前 PE 中位数为 53.6，对比历史数据（推断）处于中等偏上水平。

        以上判断存在不确定因素，待验证。
        """
        result = validate_stage_output("industry_overview", output)
        assert result == []

    def test_missing_numbers(self):
        """Output without enough concrete numbers should fail 数字引用."""
        output = """
        ## 行业定义
        算力行业是指提供计算基础设施的产业链。上游、中游、下游分工明确。
        ## 政策环境
        政策支持这个行业发展。新闻中提到了一些技术突破。
        不确定这个行业会怎么样，很多结论是推断。
        """
        result = validate_stage_output("industry_overview", output)
        labels = [m["label"] for m in result]
        assert "数字引用" in labels

    def test_missing_source_attribution(self):
        """Output without source mentions should fail 来源标注."""
        output = """
        行业平均 ROE 为 8.5%，营收增速中位数为 12.3%。
        目前 PE 中位数为 53.6，毛利率中位数为 35.2%。
        上游产业链涉及芯片制造，中游包含服务器组装，下游是云服务应用。
        结论：行业处于成长期后期，有 15 家公司已披露财报。
        """
        result = validate_stage_output("industry_overview", output)
        labels = [m["label"] for m in result]
        assert "来源标注" in labels

    def test_missing_uncertainty(self):
        """Output without uncertainty labels should fail 不确定标注."""
        output = """
        行业 ROE 为 8.5%，营收增速 12.3%，PE 中位数 53.6，毛利率 35.2%。
        上游是芯片制造，中游是服务器，下游是云服务，市场份额集中度约 60%。
        政策支持力度很大，技术迭代速度约 2 年一次。
        （来源：腾讯行情 + baostock 财报）
        """
        result = validate_stage_output("industry_overview", output)
        labels = [m["label"] for m in result]
        assert "不确定标注" in labels

    def test_missing_supply_chain(self):
        """Output without supply chain analysis should fail 产业链分析."""
        output = """
        行业 ROE 为 8.5%，营收增速 12.3%，PE 中位数 53.6%。
        毛利率中位数 35.2%，负债率均值 42.1%。
        （来源：baostock 财报 + 腾讯行情）
        这些结论基于数据推断，部分待验证。
        """
        result = validate_stage_output("industry_overview", output)
        labels = [m["label"] for m in result]
        assert "产业链分析" in labels

    # ── company_deep_dive ───────────────────────────────────

    def test_company_sections_present(self):
        output = """
        | 名称 | PE | ROE(%) | 毛利率(%) | 营收增速(%) | 负债率(%) |
        |------|-----|--------|----------|-----------|---------|
        | 中国移动 | 14.2 | 2.1 | 25.4 | 2.3 | 14.0 |
        | 工业富联 | 37.2 | 6.2 | 7.3 | 12.1 | 5.4 |
        | 寒武纪 | 120 | -5.1 | 65.0 | 30.2 | 8.1 |

        基于毛利率推断，寒武纪可能采取差异化策略，工业富联可能采取成本领先。
        中国移动高ROE但低负债率推断靠经营质量驱动。
        工业富联低毛利率+低负债率为真增长（营收+利润双增）。
        营收增速 12.3%、净利增速 10.5%、毛利率 35%、ROE 8.5%、PE 53.6。

        预警信号：寒武纪 高PE+低ROE为异常组合，可能存在估值风险。
        以上均为基于财务数据的推断。

        补充数字：ROE 8.5%、毛利率 35%、PE 53.6、营收增速 12%、净利增速 10%、负债率 42%。
        """
        result = validate_stage_output("company_deep_dive", output)
        assert result == []

    def test_missing_table(self):
        """Output without markdown table should fail Markdown表格."""
        output = """
        中国移动 ROE 2.1%，毛利率 25.4%，营收增速 2.3%
        工业富联 ROE 6.2%，毛利率 7.3%，营收增速 12.1%
        寒武纪 ROE -5.1%，毛利率 65.0%，营收增速 30.2%
        推断：寒武纪可能采取差异化策略。工业富联为成本领先，数据推断。
        预警：寒武纪高PE+低ROE存在风险。以上均基于数据推断。
        """
        result = validate_stage_output("company_deep_dive", output)
        labels = [m["label"] for m in result]
        assert "Markdown表格" in labels

    # ── investment_thesis ────────────────────────────────────

    def test_thesis_sections_present(self):
        output = """
        行业目前处于复苏阶段，PE 中位数 53.6，ROE 均值 8.5%，营收增速中位数 12.3%。

        ## Red Team 反方观点
        看空逻辑1：高PE + 低ROE，均值 8.5% 远低于市场平均。
        看空逻辑2：估值风险，PE 53.6 对应营收增速 12.3%，PEG 偏高。
        看空逻辑3：已有 3 家公司负债率超过 60%。

        如果经济复苏低于预期，上述投资方向可能被证伪。

        | 风险类型 | 判断依据 |
        |---------|---------|
        | 估值风险 | PE中位数 53.6 |
        | 财务风险 | 3家负债率>60% |
        | 政策风险 | 公告中无明确负面政策 |

        净利增速 15%、营收增速 12%、毛利率 35%、负债率 42%。
        """
        result = validate_stage_output("investment_thesis", output)
        assert result == []

    def test_missing_red_team(self):
        """Output without Red Team should fail."""
        output = """
        行业处于扩张期，PE 中位数 53.6，ROE 均值 8.5%，营收增速 12.3%。

        | 风险类型 | 依据 |
        |---------|------|
        | 估值风险 | PE 53.6 |
        | 财务风险 | 负债率>60% |
        营收增速 15%、净利增速 10%、毛利率 35% 表明行业基本面良好。
        """
        result = validate_stage_output("investment_thesis", output)
        labels = [m["label"] for m in result]
        assert "Red Team" in labels

    # ── edge cases ──────────────────────────────────────────

    def test_unknown_stage_key_returns_empty(self):
        assert validate_stage_output("nonexistent_stage", "any text") == []

    def test_empty_output_all_missing(self):
        result = validate_stage_output("industry_overview", "")
        assert len(result) == 4  # all four checks fail

    def test_output_with_many_numbers(self):
        """Output with 12+ concrete numbers and all sections should pass."""
        output = """
        行业 ROE 8.5%、12.3%、25 家、PE 53.6、毛利率 35.2%、负债率 42.1%
        上游/中游/下游，市值约 83000 亿，成分股 20 只，营收增速 15%
        （来源：腾讯 + baostock）这些结论是推断，待验证。
        """
        result = validate_stage_output("industry_overview", output)
        assert result == []


class TestBuildChasePrompt:
    """build_chase_prompt — construct follow-up for missing sections."""

    def test_empty_missing_returns_empty(self):
        result = build_chase_prompt("industry_overview", [], "previous output")
        assert result == ""

    def test_single_missing_item(self):
        missing = [{"label": "数字引用", "hint": "请补充具体数字"}]
        result = build_chase_prompt("industry_overview", missing, "prev")
        assert "数字引用" in result
        assert "补充" in result

    def test_multiple_missing_items(self):
        missing = [
            {"label": "数字引用", "hint": "请补充具体数字"},
            {"label": "来源标注", "hint": "请标注数据来源"},
        ]
        result = build_chase_prompt("industry_overview", missing, "prev")
        assert "数字引用" in result
        assert "来源标注" in result

    def test_does_not_contain_previous_output(self):
        """Chase prompt should be a fresh request, not include full original output."""
        missing = [{"label": "Red Team", "hint": "补充反方观点"}]
        result = build_chase_prompt("investment_thesis", missing, "VERY_LONG_PREVIOUS_OUTPUT" * 50)
        assert "VERY_LONG_PREVIOUS_OUTPUT" not in result

    def test_instructs_conciseness(self):
        missing = [{"label": "数字引用", "hint": "补充数字"}]
        result = build_chase_prompt("industry_overview", missing, "prev")
        assert "只输出上述补充内容" in result
        assert "不需要重新写完整报告" in result


class TestMergeChaseOutput:
    """merge_chase_output — append supplementary content."""

    def test_empty_chase_returns_original(self):
        original = "原始报告内容"
        result = merge_chase_output(original, "")
        assert result == original

    def test_whitespace_only_chase_returns_original(self):
        original = "原始报告内容"
        result = merge_chase_output(original, "  \n  ")
        assert result == original

    def test_non_empty_chase_appends_with_separator(self):
        original = "## 原始报告"
        chase = "## 补充的行业定义"
        result = merge_chase_output(original, chase)
        assert "---" in result
        assert "📌 补充内容" in result
        assert chase in result
        assert result.startswith(original)

    def test_cjk_content_preserved(self):
        original = "## 行业全景\n这是一份详细的分析报告。"
        chase = "## 补充\n市场空间约5000亿。"
        result = merge_chase_output(original, chase)
        assert "行业全景" in result
        assert "5000亿" in result
