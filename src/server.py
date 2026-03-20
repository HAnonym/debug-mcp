"""
Debug MCP Server - 基于 FastMCP 的调试 Agent 服务（优化版）
- 扩展更多工具
- 添加配置支持
- 改进日志
"""

import os
import sys
from typing import Optional

try:
    from fastmcp import FastMCP
    HAS_FASTMCP = True
except ImportError:
    HAS_FASTMCP = False
    FastMCP = None

from .agent import DebugAgent, create_agent
from .config import get_config, DebugMCPConfig
from .logger import get_logger, init_default_logger
from .memory import get_memory

logger = get_logger("debug-mcp.server")

_mcp_server: Optional[object] = None


def get_server(name: str = "debug-mcp", config: DebugMCPConfig = None) -> object:
    global _mcp_server

    if _mcp_server is not None:
        return _mcp_server

    if not HAS_FASTMCP:
        raise ImportError("请安装 fastmcp: pip install fastmcp")

    # 初始化日志
    init_default_logger()

    _mcp_server = FastMCP(name)
    _register_tools(_mcp_server, config)

    return _mcp_server


def _register_tools(server: object, config: DebugMCPConfig = None):

    @server.tool()
    def debug(error: str, auto_save: bool = True) -> str:
        """排查问题 - 输入错误信息，返回解决方案"""
        logger.info(f"Debug request: {error[:50]}...")
        agent = create_agent()
        result = agent.debug(error, auto_save)

        if result['found_in_history']:
            output = f"🔍 找到历史案例 (出现 {result['history_case'].get('occurrences', 0)} 次)\n\n"
        else:
            output = "🔍 新问题，开始排查...\n\n"

        if result.get('root_cause'):
            output += f"📍 根因:\n{result['root_cause']}\n\n"

        if result.get('solution'):
            output += f"✅ 解决方案:\n{result['solution']}\n\n"

        if result.get('prevention'):
            output += f"🛡️ 预防建议:\n{result['prevention']}"

        if result.get('error'):
            output += f"\n\n⚠️ 错误: {result['error']}"

        return output

    @server.tool()
    def search_case(keywords: str, limit: int = 20) -> str:
        """搜索历史案例"""
        agent = create_agent()
        cases = agent.search_cases(keywords, limit=limit)

        if not cases:
            return f"未找到包含 '{keywords}' 的案例"

        output = f"找到 {len(cases)} 个相关案例:\n\n"

        for i, case in enumerate(cases[:10], 1):
            output += f"{i}. [{case.get('problem_type', '未知')}] "
            output += f"{case.get('problem', '')[:50]}...\n"
            output += f"   关键词: {', '.join(case.get('keywords', [])[:5])}\n"
            output += f"   出现次数: {case.get('occurrences', 0)}\n\n"

        return output

    @server.tool()
    def list_cases(limit: int = 20) -> str:
        """列出所有历史案例"""
        agent = create_agent()
        cases = agent.list_cases(limit)

        if not cases:
            return "暂无历史案例"

        output = f"共 {len(cases)} 个案例 (按出现次数排序):\n\n"

        for i, case in enumerate(cases, 1):
            output += f"{i}. {case.get('problem', '')[:40]}...\n"
            output += f"   类型: {case.get('problem_type', '未知')} | "
            output += f"出现: {case.get('occurrences', 0)} 次\n"

        return output

    @server.tool()
    def get_stats() -> str:
        """获取记忆系统统计信息"""
        agent = create_agent()
        stats = agent.get_stats()

        output = "📊 记忆系统统计\n\n"
        output += f"- 总案例数: {stats['total_cases']}\n"
        output += f"- 总排查次数: {stats['total_occurrences']}\n"
        output += f"- 问题类型数: {stats.get('unique_problem_types', len(stats['problem_types']))}\n\n"

        if stats.get('problem_types'):
            output += "问题类型分布:\n"
            for ptype, count in stats['problem_types'].items():
                output += f"  - {ptype}: {count}\n"

        return output

    @server.tool()
    def clear_memory() -> str:
        """清空所有记忆"""
        memory = get_memory()
        memory.clear()
        logger.warning("Memory cleared via MCP")
        return "✅ 记忆已清空"

    @server.tool()
    def search_code(keyword: str, limit: int = 50) -> str:
        """搜索代码文件"""
        from .tools import get_tools
        tools = get_tools()
        return tools.search_code(keyword, limit=limit)

    @server.tool()
    def read_file(filepath: str, lines: int = 100, offset: int = 0) -> str:
        """读取文件内容"""
        from .tools import get_tools
        tools = get_tools()
        return tools.read_file(filepath, lines=lines, offset=offset)

    @server.tool()
    def grep(pattern: str, path: str = None, context: int = 2) -> str:
        """正则搜索代码"""
        from .tools import get_tools
        tools = get_tools()
        return tools.grep(pattern, path=path, context=context)

    @server.tool()
    def check_syntax(filepath: str) -> str:
        """检查文件语法"""
        from .tools import get_tools
        tools = get_tools()
        return tools.check_syntax(filepath)

    @server.tool()
    def list_files(pattern: str = "*", recursive: bool = True) -> str:
        """列出匹配的文件"""
        from .tools import get_tools
        tools = get_tools()
        return tools.list_files(pattern=pattern, recursive=recursive)

    @server.tool()
    def refresh_index() -> str:
        """刷新文件索引"""
        agent = create_agent()
        agent.refresh_index()
        logger.info("File index refreshed")
        return "✅ 文件索引已刷新"

    @server.tool()
    def get_case(case_id: str) -> str:
        """获取指定案例详情"""
        memory = get_memory()
        case = memory.get_case(case_id)

        if not case:
            return f"未找到案例: {case_id}"

        output = f"案例详情 (ID: {case_id})\n\n"
        output += f"问题: {case.get('problem', '')}\n\n"
        output += f"类型: {case.get('problem_type', '未知')}\n"
        output += f"关键词: {', '.join(case.get('keywords', []))}\n"
        output += f"出现次数: {case.get('occurrences', 0)}\n"
        output += f"创建时间: {case.get('created_at', '')}\n\n"

        if case.get('root_cause'):
            output += f"根因: {case['root_cause']}\n\n"
        if case.get('solution'):
            output += f"解决方案: {case['solution']}\n\n"
        if case.get('prevention'):
            output += f"预防建议: {case['prevention']}\n"

        return output

    @server.tool()
    def delete_case(case_id: str) -> str:
        """删除指定案例"""
        memory = get_memory()
        if memory.delete_case(case_id):
            logger.info(f"Deleted case: {case_id}")
            return f"✅ 案例已删除: {case_id}"
        return f"❌ 未找到案例: {case_id}"

    @server.tool()
    def mark_effective(case_id: str, effective: bool = True) -> str:
        """
        标记案例解决方案是否有效

        Args:
            case_id: 案例ID
            effective: True=有效, False=无效
        """
        memory = get_memory()
        if memory.mark_effective(case_id, effective):
            status = "✅ 方案有效" if effective else "❌ 方案无效"
            return f"{status}，感谢反馈！这将帮助改进匹配算法。"
        return f"❌ 未找到案例: {case_id}"

    @server.tool()
    def get_recommended_fixes(min_rating: float = 0.5, limit: int = 10) -> str:
        """
        获取高评价的有效解决方案

        Args:
            min_rating: 最低评分 (0-1)
            limit: 返回数量
        """
        memory = get_memory()
        cases = memory.get_effective_cases(min_rating, limit)

        if not cases:
            return "暂无高评价方案"

        output = f"⭐ 高评价解决方案 (评分 >= {min_rating}):\n\n"

        for i, case in enumerate(cases, 1):
            rating = case.get('user_rating', 0)
            output += f"{i}. [{case.get('problem_type', 'unknown')}] "
            output += f"{case.get('problem', '')[:40]}...\n"
            output += f"   评分: {rating:.0%} | 出现: {case.get('occurrences', 0)} 次\n"
            if case.get('solution'):
                output += f"   方案: {case.get('solution')[:80]}...\n"
            output += "\n"

        return output

    @server.tool()
    def pre_check_code(code: str = None, filepath: str = None, action: str = None) -> str:
        """
        主动预防：检查代码中可能的风险模式

        Args:
            code: 要检查的代码字符串
            filepath: 要检查的文件路径
            action: 正在尝试的操作描述（如 "用 try-catch 包裹"）
        """
        agent = create_agent()
        result = agent.pre_check(code=code, filepath=filepath, action=action)

        if not result.get('success'):
            return f"⚠️ 检查失败: {result.get('error')}"

        output = "🔍 代码风险预检结果:\n\n"

        # 1. 如果有尝试操作检查结果
        if result.get('action_check'):
            output += result['action_check']['warning'] + "\n\n"
            for failed in result['action_check'].get('failed_solutions', []):
                output += f"  ❌ 历史无效方案: {failed.get('problem')}\n"
                output += f"     原因: {failed.get('root_cause')}\n"

        # 2. 风险检测结果
        if result.get('risks'):
            output += "⚠️ 检测到以下风险:\n"
            for risk in result['risks']:
                output += f"- {risk['description']} ({risk['matches']} 处)\n"
                output += f"  💡 建议: {risk.get('suggestion', '')}\n"
            output += "\n"

        # 3. 历史建议
        if result.get('suggestions'):
            output += "📝 相关建议:\n"
            for sug in result['suggestions'][:5]:
                if sug.get('message'):
                    output += f"- {sug['message']}\n"
                elif sug.get('related_problem'):
                    output += f"- 历史类似问题: {sug['related_problem']}\n"
                    if sug.get('root_cause'):
                        output += f"  根因: {sug['root_cause']}\n"

        output += f"\n✅ 已检查 {result.get('checked_count', 0)} 个相关案例"

        return output

    @server.tool()
    def get_weekly_report() -> str:
        """获取本周错误报告"""
        memory = get_memory()
        report = memory.get_weekly_report()

        output = "📊 本周错误报告\n\n"
        output += f"📅 周期: {report.get('period', '')}\n"
        output += f"🆕 新增案例: {report.get('week_new_cases', 0)} 个\n"
        output += f"📈 总排查次数: {report.get('week_total_occurrences', 0)} 次\n\n"

        top_errors = report.get('top_errors', [])
        if top_errors:
            output += "🔥 本周高频错误 TOP 10:\n"
            for i, err in enumerate(top_errors, 1):
                output += f"  {i}. [{err['type']}] {err['problem']}\n"
                output += f"     出现: {err['count']} 次\n"

        return output

    @server.tool()
    def get_error_trends(days: int = 30) -> str:
        """
        获取错误趋势分析

        Args:
            days: 统计天数 (默认30天)
        """
        memory = get_memory()
        trends = memory.get_error_trends(days)

        output = f"📈 错误趋势分析 (最近 {trends.get('period_days', days)} 天)\n\n"
        output += f"📊 总排查次数: {trends.get('total_occurrences', 0)}\n"
        output += f"📈 日均排查: {trends.get('daily_average', 0)} 次\n"
        output += f"📉 趋势: {trends.get('trend', '未知')}\n\n"

        top_types = trends.get('top_problem_types', [])
        if top_types:
            output += "🔝 问题类型排行:\n"
            for i, t in enumerate(top_types, 1):
                output += f"  {i}. {t['type']}: {t['count']} 次\n"

        return output


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Debug MCP Server

用法:
  debug-mcp              # 启动服务器
  debug-mcp --help       # 显示帮助

环境变量:
  DEEPSEEK_API_KEY       # DeepSeek API Key
  DEEPSEEK_BASE_URL      # API 地址 (默认: https://api.deepseek.com)
  DEBUG_MCP_MODEL        # 模型名称 (默认: deepseek-chat)
  DEBUG_MCP_TIMEOUT      # 超时时间 (默认: 30)
  DEBUG_MCP_WORKSPACE    # 工作区路径
  DEBUG_MCP_LOG_LEVEL    # 日志级别 (默认: INFO)

示例:
  export DEEPSEEK_API_KEY=sk-xxx
  debug-mcp
        """)
        return

    try:
        server = get_server()
        print("🚀 Debug MCP Server 启动中...")
        print("📝 可用工具:")
        print("   - debug: 排查问题")
        print("   - search_case: 搜索案例")
        print("   - list_cases: 列出案例")
        print("   - get_case: 查看案例详情")
        print("   - delete_case: 删除案例")
        print("   - mark_effective: 标记方案有效性")
        print("   - get_recommended_fixes: 高评价方案")
        print("   - pre_check_code: 代码风险预检")
        print("   - get_weekly_report: 周报")
        print("   - get_error_trends: 趋势分析")
        print("   - get_stats: 统计信息")
        print("   - clear_memory: 清空记忆")
        print("   - search_code: 搜索代码")
        print("   - read_file: 读取文件")
        print("   - grep: 正则搜索")
        print("   - check_syntax: 语法检查")
        print("   - list_files: 列出文件")
        print("   - refresh_index: 刷新索引")
        server.run()
    except ImportError as e:
        print(f"❌ 错误: {e}")
        print("💡 请安装依赖: pip install fastmcp httpx python-dotenv tenacity")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
