"""
日志分析器 - 分析日志文件找出问题
"""

import re
import os
from typing import Dict, List, Optional
from collections import Counter
from dataclasses import dataclass


@dataclass
class LogIssue:
    """日志问题"""
    level: str  # ERROR, WARNING, INFO
    message: str
    line_number: int
    count: int = 1


@dataclass
class LogAnalysis:
    """日志分析结果"""
    total_lines: int
    error_count: int
    warning_count: int
    issues: List[LogIssue]
    patterns: Dict[str, int]
    recommendations: List[str]


class LogAnalyzer:
    """日志分析器"""

    # 日志级别模式
    LEVEL_PATTERNS = {
        'ERROR': re.compile(r'\b(ERROR|ERR|FATAL|CRITICAL)\b', re.IGNORECASE),
        'WARNING': re.compile(r'\b(WARNING|WARN)\b', re.IGNORECASE),
        'INFO': re.compile(r'\b(INFO)\b', re.IGNORECASE),
    }

    # 常见错误模式
    ERROR_PATTERNS = [
        (r'connection refused', '连接被拒绝'),
        (r'timeout', '请求超时'),
        (r'permission denied', '权限不足'),
        (r'not found', '资源未找到'),
        (r'out of memory', '内存不足'),
        (r'null', '空指针'),
        (r'exception', '异常'),
        (r'failed', '失败'),
        (r'invalid', '无效'),
    ]

    def analyze_file(self, filepath: str, max_lines: int = 10000) -> LogAnalysis:
        """
        分析日志文件

        Args:
            filepath: 日志文件路径
            max_lines: 最大读取行数

        Returns:
            LogAnalysis 对象
        """
        if not os.path.exists(filepath):
            return LogAnalysis(
                total_lines=0,
                error_count=0,
                warning_count=0,
                issues=[],
                patterns={},
                recommendations=["文件不存在"]
            )

        lines = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if i > max_lines:
                        break
                    lines.append((i, line.strip()))
        except Exception as e:
            return LogAnalysis(
                total_lines=0,
                error_count=0,
                warning_count=0,
                issues=[],
                patterns={},
                recommendations=[f"读取文件失败: {e}"]
            )

        return self.analyze_lines(lines)

    def analyze_text(self, text: str) -> LogAnalysis:
        """分析日志文本"""
        lines = [(i + 1, line) for i, line in enumerate(text.strip().split('\n'))]
        return self.analyze_lines(lines)

    def analyze_lines(self, lines: List[tuple]) -> LogAnalysis:
        """分析日志行"""
        issues = []
        error_count = 0
        warning_count = 0
        pattern_counts = Counter()

        for line_num, line in lines:
            if not line:
                continue

            # 检测日志级别
            level = self._detect_level(line)

            if level == 'ERROR':
                error_count += 1
                issues.append(LogIssue(
                    level='ERROR',
                    message=line[:200],
                    line_number=line_num
                ))
            elif level == 'WARNING':
                warning_count += 1
                issues.append(LogIssue(
                    level='WARNING',
                    message=line[:200],
                    line_number=line_num
                ))

            # 检测错误模式
            for pattern, desc in self.ERROR_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    pattern_counts[desc] += 1

        # 生成建议
        recommendations = self._generate_recommendations(
            error_count, warning_count, pattern_counts
        )

        return LogAnalysis(
            total_lines=len(lines),
            error_count=error_count,
            warning_count=warning_count,
            issues=issues,
            patterns=dict(pattern_counts),
            recommendations=recommendations
        )

    def _detect_level(self, line: str) -> Optional[str]:
        """检测日志级别"""
        for level, pattern in self.LEVEL_PATTERNS.items():
            if pattern.search(line):
                return level
        return None

    def _generate_recommendations(self, error_count: int, warning_count: int,
                                   patterns: Counter) -> List[str]:
        """生成建议"""
        recs = []

        if error_count == 0:
            recs.append("✅ 没有发现错误")
        else:
            recs.append(f"❌ 发现 {error_count} 个错误")

        if warning_count > 0:
            recs.append(f"⚠️  发现 {warning_count} 个警告")

        # 基于模式给出建议
        if patterns.get('connection refused', 0) > 0:
            recs.append("🔧 网络连接问题：检查服务是否运行，网络是否正常")

        if patterns.get('timeout', 0) > 0:
            recs.append("🔧 超时问题：增加超时时间，优化查询性能")

        if patterns.get('permission denied', 0) > 0:
            recs.append("🔧 权限问题：检查文件/目录权限设置")

        if patterns.get('null', 0) > 0:
            recs.append("🔧 空值问题：添加空值检查，使用 optional chaining")

        if patterns.get('out of memory', 0) > 0:
            recs.append("🔧 内存问题：检查内存泄漏，增加内存限制")

        if patterns.get('exception', 0) > 5:
            recs.append("🔧 异常频繁：需要深入排查异常根因")

        if not recs:
            recs.append("日志分析完成，未发现明显问题")

        return recs

    def format_summary(self, analysis: LogAnalysis) -> str:
        """格式化摘要"""
        output = []

        output.append("📊 日志分析报告")
        output.append("=" * 50)
        output.append(f"总行数: {analysis.total_lines}")
        output.append(f"错误: {analysis.error_count} | 警告: {analysis.warning_count}")
        output.append("")

        if analysis.issues:
            output.append("🚨 主要问题:")
            for issue in analysis.issues[:10]:
                output.append(f"  [{issue.level}] 第{issue.line_number}行: {issue.message[:80]}")
            output.append("")

        if analysis.patterns:
            output.append("📈 错误模式统计:")
            sorted_patterns = sorted(analysis.patterns.items(), key=lambda x: -x[1])
            for pattern, count in sorted_patterns[:10]:
                output.append(f"  - {pattern}: {count}次")
            output.append("")

        output.append("💡 建议:")
        for rec in analysis.recommendations:
            output.append(f"  {rec}")

        return "\n".join(output)


def analyze_log_file(filepath: str, max_lines: int = 10000) -> LogAnalysis:
    """便捷函数：分析日志文件"""
    analyzer = LogAnalyzer()
    return analyzer.analyze_file(filepath, max_lines)


def analyze_log_text(text: str) -> LogAnalysis:
    """便捷函数：分析日志文本"""
    analyzer = LogAnalyzer()
    return analyzer.analyze_text(text)
