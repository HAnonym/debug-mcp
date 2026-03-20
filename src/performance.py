"""
性能分析器 - 识别代码性能问题
"""

import re
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PerformanceIssue:
    """性能问题"""
    type: str  # n_plus_1, slow_query, memory_leak, etc.
    severity: str  # high, medium, low
    file: str
    line: int
    description: str
    suggestion: str


class PerformanceAnalyzer:
    """性能分析器"""

    # 性能问题模式
    PATTERNS = {
        # N+1 查询问题
        'n_plus_1': {
            'patterns': [
                r'for\s+\w+\s+in\s+\w+:\s*\n\s*.*\.query\(',
                r'for\s+\w+\s+in\s+\w+:\s*\n\s*.*\.get\(',
                r'\.all\(\).*for\s+\w+\s+in',
            ],
            'description': 'N+1 查询问题',
            'severity': 'high',
            'suggestion': '使用批量查询或预加载 (prefetch_related/select_related)'
        },
        # 循环中查询
        'loop_query': {
            'patterns': [
                r'for\s+.*:\s*\n\s*.*\.filter\(',
                r'for\s+.*:\s*\n\s*.*\.find\(',
                r'while\s+.*:\s*\n\s*.*\.query\(',
            ],
            'description': '循环中执行数据库查询',
            'severity': 'high',
            'suggestion': '将循环内的查询移到循环外，使用批量查询'
        },
        # 慢查询
        'slow_query': {
            'patterns': [
                r'\.filter\([^)]*\)\.filter\([^)]*\)',
                r'\.filter\([^)]*\)\.order_by\(',
                r'SELECT.*FROM.*WHERE.*OR.',
                r'LIKE\s+[\'"]%',
            ],
            'description': '可能存在性能问题的查询',
            'severity': 'medium',
            'suggestion': '添加索引，使用覆盖索引，避免全表扫描'
        },
        # 内存泄漏模式
        'memory_leak': {
            'patterns': [
                r'global\s+\w+',
                r'\w+\s*=\s*\[\].*while.*append',
                r'cache\.set\([^)]+\)\s*#.*never.*clear',
                r'event\.on\([^)]+\)\s*#.*never.*remove',
            ],
            'description': '可能的内存泄漏模式',
            'severity': 'high',
            'suggestion': '确保缓存/事件监听器有清理机制'
        },
        # 大数据加载
        'large_data': {
            'patterns': [
                r'\.all\(\)',
                r'\.objects\.all\(\)',
                r'fetchAll\(\)',
                r'JSON\.parse\([^)]*\)',  # 大 JSON 解析
            ],
            'description': '一次性加载大量数据',
            'severity': 'medium',
            'suggestion': '使用分页或流式处理'
        },
        # 同步阻塞
        'sync_block': {
            'patterns': [
                r'time\.sleep\(',
                r'\.join\(\)',
                r'requests\.get\(',
                r'requests\.post\(',
            ],
            'description': '同步阻塞操作',
            'severity': 'medium',
            'suggestion': '使用异步操作 (async/await)'
        },
        # 递归无限制
        'recursive_no_limit': {
            'patterns': [
                r'def\s+\w+\([^)]*\):\s*\n\s*return\s+\w+\(',
                r'function\s+\w+\([^)]*\)\s*{\s*return\s+\w+\(',
            ],
            'description': '递归调用无深度限制',
            'severity': 'medium',
            'suggestion': '添加递归深度限制或改用迭代'
        },
        # 正则回溯
        'regex_backtrack': {
            'patterns': [
                r'\.\*\+',
                r'\.\*\*\+',
                r'\+.*\*',
            ],
            'description': '可能存在正则表达式回溯问题',
            'severity': 'low',
            'suggestion': '优化正则表达式，避免贪婪匹配'
        },
    }

    def analyze_file(self, filepath: str) -> List[PerformanceIssue]:
        """分析单个文件"""
        issues = []

        if not os.path.exists(filepath):
            return issues

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                content = ''.join(lines)
        except Exception:
            return issues

        # 检测各种模式
        for issue_type, config in self.PATTERNS.items():
            for pattern in config['patterns']:
                try:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                    for match in matches:
                        # 计算行号
                        line_num = content[:match.start()].count('\n') + 1

                        issues.append(PerformanceIssue(
                            type=issue_type,
                            severity=config['severity'],
                            file=filepath,
                            line=line_num,
                            description=config['description'],
                            suggestion=config['suggestion']
                        ))
                except re.error:
                    continue

        return issues

    def analyze_workspace(self, workspace: str) -> Dict:
        """分析整个工作区"""
        issues = []
        files_scanned = 0

        for root, dirs, files in os.walk(workspace):
            # 排除目录
            dirs[:] = [d for d in dirs if d not in
                      ('.git', '__pycache__', 'node_modules', '.venv', 'venv')]

            for file in files:
                if file.endswith(('.py', '.js', '.ts')):
                    filepath = os.path.join(root, file)
                    file_issues = self.analyze_file(filepath)
                    issues.extend(file_issues)
                    files_scanned += 1

        # 按严重程度分组
        by_severity = {'high': [], 'medium': [], 'low': []}
        for issue in issues:
            by_severity[issue.severity].append(issue)

        return {
            'files_scanned': files_scanned,
            'total_issues': len(issues),
            'issues': issues,
            'by_severity': by_severity,
            'summary': self._generate_summary(by_severity)
        }

    def _generate_summary(self, by_severity: Dict) -> List[str]:
        """生成摘要"""
        summary = []

        high = len(by_severity['high'])
        medium = len(by_severity['medium'])
        low = len(by_severity['low'])

        if high > 0:
            summary.append(f"🔴 高严重: {high} 个问题需要立即处理")
        if medium > 0:
            summary.append(f"🟡 中严重: {medium} 个问题建议优化")
        if low > 0:
            summary.append(f"🟢 低严重: {low} 个问题可后续处理")

        if not summary:
            summary.append("✅ 未发现明显性能问题")

        return summary

    def format_report(self, result: Dict) -> str:
        """格式化报告"""
        output = []

        output.append("📊 性能分析报告")
        output.append("=" * 50)
        output.append(f"扫描文件: {result['files_scanned']}")
        output.append(f"发现问题: {result['total_issues']}")
        output.append("")

        # 摘要
        output.append("📈 摘要:")
        for line in result['summary']:
            output.append(f"  {line}")
        output.append("")

        # 高严重问题
        if result['by_severity']['high']:
            output.append("🔴 高严重问题:")
            for issue in result['by_severity']['high'][:5]:
                output.append(f"  • {issue.description}")
                output.append(f"    文件: {issue.file}:{issue.line}")
                output.append(f"    建议: {issue.suggestion}")
            output.append("")

        # 中严重问题
        if result['by_severity']['medium']:
            output.append("🟡 中严重问题:")
            for issue in result['by_severity']['medium'][:5]:
                output.append(f"  • {issue.description}")
                output.append(f"    文件: {issue.file}:{issue.line}")
            output.append("")

        return "\n".join(output)


def analyze_performance(workspace: str = None) -> Dict:
    """便捷函数：分析性能"""
    analyzer = PerformanceAnalyzer()
    return analyzer.analyze_workspace(workspace or os.getcwd())


def format_performance_report(result: Dict) -> str:
    """便捷函数：格式化报告"""
    analyzer = PerformanceAnalyzer()
    return analyzer.format_report(result)
