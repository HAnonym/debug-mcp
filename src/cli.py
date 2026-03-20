"""
CLI - 命令行工具增强
"""

import argparse
import sys
import os
from typing import Optional

from .agent import DebugAgent, create_agent
from .memory import get_memory
from .test_runner import TestRunner, get_test_info
from .local_db import search_errors, get_all_categories
from .logger import init_default_logger, get_logger
from .stack_parser import format_stack_summary
from .log_analyzer import LogAnalyzer
from .patch_generator import PatchGenerator
from .performance import PerformanceAnalyzer
from .security import SecurityScanner
from .code_metrics import CodeMetrics

logger = get_logger("debug-mcp.cli")


def cmd_fix(args):
    """修复命令"""
    agent = create_agent()

    if args.stdin:
        # 从 stdin 读取错误
        error = sys.stdin.read().strip()
    else:
        error = args.error

    if not error:
        print("Error: 请输入错误信息或使用 --stdin 从管道输入")
        return 1

    print(f"🔍 分析错误: {error[:80]}...")
    print("-" * 50)

    result = agent.debug(error, auto_save=args.save)

    if result.get('root_cause'):
        print(f"\n📍 根因:")
        print(f"   {result['root_cause']}")

    if result.get('solution'):
        print(f"\n✅ 解决方案:")
        print(f"   {result['solution']}")

    if result.get('prevention'):
        print(f"\n🛡️ 预防建议:")
        print(f"   {result['prevention']}")

    print(f"\n模式: {result.get('mode', 'unknown')}")

    return 0 if result.get('success') else 1


def cmd_explain(args):
    """解释错误命令"""
    agent = create_agent()

    if args.stdin:
        error = sys.stdin.read().strip()
    else:
        error = args.error

    if not error:
        print("Error: 请输入错误信息")
        return 1

    print(f"📖 解释错误: {error[:80]}...")
    print("-" * 50)

    # 使用本地模式解释
    result = agent.debug(error, auto_save=False, use_llm=False)

    if result.get('root_cause'):
        print(f"\n📍 根因:")
        print(f"   {result['root_cause']}")

    if result.get('solution'):
        print(f"\n💡 解释:")
        # 提取解决方案中的关键信息
        solution = result.get('solution', '')
        lines = solution.split('\n')
        for line in lines[:10]:
            if line.strip():
                print(f"   {line}")

    return 0


def cmd_history(args):
    """历史记录命令"""
    memory = get_memory()

    if args.clear:
        memory.clear()
        print("✅ 历史记录已清空")
        return 0

    # 获取案例
    cases = memory.list_cases(limit=args.limit)

    if not cases:
        print("暂无历史记录")
        return 0

    print(f"📚 历史记录 (共 {len(cases)} 条)")
    print("-" * 50)

    for i, case in enumerate(cases, 1):
        problem = case.get('problem', '')[:50]
        occurrences = case.get('occurrences', 0)
        ptype = case.get('problem_type', 'unknown')

        print(f"\n{i}. [{ptype}] {problem}...")
        print(f"   出现次数: {occurrences}")

    return 0


def cmd_stats(args):
    """统计命令"""
    memory = get_memory()
    stats = memory.get_stats()

    print("📊 统计信息")
    print("-" * 50)
    print(f"总案例数: {stats['total_cases']}")
    print(f"总排查次数: {stats['total_occurrences']}")
    print(f"问题类型数: {stats.get('unique_problem_types', len(stats['problem_types']))}")

    if stats.get('problem_types'):
        print("\n问题类型分布:")
        for ptype, count in stats['problem_types'].items():
            bar = "█" * (count * 2)
            print(f"  {ptype}: {count} {bar}")

    return 0


def cmd_search(args):
    """搜索错误模式"""
    keyword = args.keyword

    print(f"🔍 搜索: {keyword}")
    print("-" * 50)

    results = search_errors(keyword)

    if not results:
        print("未找到相关错误类型")
        # 显示所有分类
        print("\n可用的错误分类:")
        for cat in get_all_categories():
            print(f"  - {cat}")
        return 0

    print(f"找到 {len(results)} 个相关错误类型:\n")

    for r in results:
        print(f"  • {r['name']} ({r['category']})")

    return 0


def cmd_test(args):
    """测试运行命令"""
    runner = TestRunner(args.workspace or os.getcwd())

    if args.info:
        info = runner.get_test_info()
        print("🧪 测试环境信息")
        print("-" * 50)
        print(f"工作区: {info['workspace']}")
        print(f"检测框架: {info['framework'] or '未检测到'}")
        print(f"可用框架: {', '.join(info['available']) if info['available'] else '无'}")
        return 0

    print("🧪 运行测试...")
    print("-" * 50)

    result = runner.run_tests(pattern=args.pattern)

    print(result.get('output', ''))

    if result.get('success'):
        print("\n✅ 测试通过")
    else:
        print(f"\n❌ 测试失败: {result.get('error', 'Unknown error')}")

    return 0 if result.get('success') else 1


def cmd_server(args):
    """启动服务器"""
    from .server import get_server

    print("🚀 启动 Debug MCP Server...")
    print("-" * 50)

    try:
        server = get_server()
        print("✅ 服务器启动成功!")
        print("📝 可用工具: debug, search_case, list_cases, get_stats, ...")
        server.run()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

    return 0


def cmd_stack(args):
    """解析堆栈跟踪"""
    if args.stdin:
        stack = sys.stdin.read().strip()
    else:
        stack = args.stack

    if not stack:
        print("Error: 请输入堆栈跟踪或使用 --stdin")
        return 1

    print("�解析堆栈跟踪...")
    print("-" * 50)
    print(format_stack_summary(stack))

    return 0


def cmd_log(args):
    """分析日志文件"""
    if args.text:
        # 分析文本
        analyzer = LogAnalyzer()
        result = analyzer.analyze_text(args.text)
        print(analyzer.format_summary(result))
    elif args.file:
        # 分析文件
        analyzer = LogAnalyzer()
        result = analyzer.analyze_file(args.file)
        print(analyzer.format_summary(result))
    else:
        print("Error: 请指定 --file 或 --text")
        return 1

    return 0


def cmd_patch(args):
    """生成修复补丁"""
    if args.stdin:
        error = sys.stdin.read().strip()
    else:
        error = args.error

    if not error:
        print("Error: 请输入错误信息")
        return 1

    # 解析错误获取文件位置
    from .stack_parser import parse_stack_trace
    parsed = parse_stack_trace(error)

    if not parsed.main_file:
        print("⚠️ 无法从错误中提取文件位置")
        print("请手动指定文件和行号: debug-mcp patch --file path --line 10 --error 'TypeError'")
        return 1

    print(f"🔧 生成修复补丁...")
    print("-" * 50)

    generator = PatchGenerator()
    fix = generator.generate_fix(
        error_type=parsed.error_type,
        file_path=parsed.main_file,
        line=parsed.main_line or 1
    )

    if fix:
        print(generator.format_suggestion(fix))
    else:
        print("❌ 无法自动生成修复")
        print("请手动修复")

    return 0


def cmd_perf(args):
    """性能分析命令"""
    workspace = args.workspace or os.getcwd()

    print(f"🔍 扫描性能问题: {workspace}")
    print("-" * 50)

    analyzer = PerformanceAnalyzer()
    result = analyzer.analyze_workspace(workspace)
    print(analyzer.format_report(result))

    return 0


def cmd_security(args):
    """安全扫描命令"""
    workspace = args.workspace or os.getcwd()

    print(f"🔒 安全扫描: {workspace}")
    print("-" * 50)

    scanner = SecurityScanner()
    result = scanner.scan_workspace(workspace)
    print(scanner.format_report(result))

    return 0


def cmd_metrics(args):
    """代码度量命令"""
    workspace = args.workspace or os.getcwd()

    print(f"📊 代码度量分析: {workspace}")
    print("-" * 50)

    analyzer = CodeMetrics()
    result = analyzer.analyze_workspace(workspace)
    print(analyzer.format_report(result))

    return 0


def main():
    """主入口"""
    # 初始化日志
    init_default_logger()

    parser = argparse.ArgumentParser(
        description="Debug MCP - 智能调试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  debug-mcp fix "TypeError: Cannot read property 'id' of undefined"
  echo "TypeError: x is undefined" | debug-mcp fix --stdin
  debug-mcp explain "ImportError: No module named 'requests'"
  debug-mcp history
  debug-mcp stats
  debug-mcp search TypeError
  debug-mcp test
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # fix 命令
    fix_parser = subparsers.add_parser('fix', help='修复错误')
    fix_parser.add_argument('error', nargs='?', help='错误信息')
    fix_parser.add_argument('--stdin', action='store_true', help='从 stdin 读取错误')
    fix_parser.add_argument('--no-save', dest='save', action='store_false', help='不保存到历史')
    fix_parser.set_defaults(func=cmd_fix)

    # explain 命令
    explain_parser = subparsers.add_parser('explain', help='解释错误（本地模式）')
    explain_parser.add_argument('error', nargs='?', help='错误信息')
    explain_parser.add_argument('--stdin', action='store_true', help='从 stdin 读取错误')
    explain_parser.set_defaults(func=cmd_explain)

    # history 命令
    history_parser = subparsers.add_parser('history', help='查看历史记录')
    history_parser.add_argument('--limit', type=int, default=20, help='显示数量')
    history_parser.add_argument('--clear', action='store_true', help='清空历史')
    history_parser.set_defaults(func=cmd_history)

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='查看统计信息')
    stats_parser.set_defaults(func=cmd_stats)

    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索错误类型')
    search_parser.add_argument('keyword', help='关键词')
    search_parser.set_defaults(func=cmd_search)

    # test 命令
    test_parser = subparsers.add_parser('test', help='运行测试')
    test_parser.add_argument('--pattern', help='测试模式过滤')
    test_parser.add_argument('--info', action='store_true', help='显示测试环境信息')
    test_parser.add_argument('--workspace', help='工作区路径')
    test_parser.set_defaults(func=cmd_test)

    # server 命令
    server_parser = subparsers.add_parser('server', help='启动 MCP 服务器')
    server_parser.set_defaults(func=cmd_server)

    # stack 命令
    stack_parser = subparsers.add_parser('stack', help='解析堆栈跟踪')
    stack_parser.add_argument('stack', nargs='?', help='堆栈跟踪文本')
    stack_parser.add_argument('--stdin', action='store_true', help='从 stdin 读取')
    stack_parser.set_defaults(func=cmd_stack)

    # log 命令
    log_parser = subparsers.add_parser('log', help='分析日志')
    log_parser.add_argument('--file', help='日志文件路径')
    log_parser.add_argument('--text', help='日志文本')
    log_parser.set_defaults(func=cmd_log)

    # patch 命令
    patch_parser = subparsers.add_parser('patch', help='生成修复补丁')
    patch_parser.add_argument('error', nargs='?', help='错误信息')
    patch_parser.add_argument('--stdin', action='store_true', help='从 stdin 读取')
    patch_parser.add_argument('--file', help='源文件路径')
    patch_parser.add_argument('--line', type=int, default=1, help='错误行号')
    patch_parser.set_defaults(func=cmd_patch)

    # perf 命令
    perf_parser = subparsers.add_parser('perf', help='性能分析')
    perf_parser.add_argument('--workspace', help='工作区路径')
    perf_parser.set_defaults(func=cmd_perf)

    # security 命令
    security_parser = subparsers.add_parser('security', help='安全扫描')
    security_parser.add_argument('--workspace', help='工作区路径')
    security_parser.set_defaults(func=cmd_security)

    # metrics 命令
    metrics_parser = subparsers.add_parser('metrics', help='代码度量')
    metrics_parser.add_argument('--workspace', help='工作区路径')
    metrics_parser.set_defaults(func=cmd_metrics)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
