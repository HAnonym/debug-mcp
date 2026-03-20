"""
网络请求分析器 - 分析 HTTP 请求/响应问题
"""

import re
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class HTTPIssue:
    """HTTP 问题"""
    type: str  # timeout, connection_error, 4xx, 5xx, redirect, ssl_error
    severity: str  # high, medium, low
    url: str
    message: str
    suggestion: str


class HTTPAnalyzer:
    """网络请求分析器"""

    # HTTP 状态码分类
    STATUS_CATEGORIES = {
        '4xx': {
            '400': '请求语法错误',
            '401': '未认证',
            '403': '无权限',
            '404': '资源不存在',
            '429': '请求过于频繁',
        },
        '5xx': {
            '500': '服务器内部错误',
            '502': '网关错误',
            '503': '服务不可用',
            '504': '网关超时',
        }
    }

    # 问题模式
    ISSUE_PATTERNS = {
        'timeout': re.compile(r'(timeout|timed?\s*out)', re.IGNORECASE),
        'connection_refused': re.compile(r'(connection\s+refused|ECONNREFUSED)', re.IGNORECASE),
        'ssl_error': re.compile(r'(SSL|TLS|certificate|ssl)', re.IGNORECASE),
        'dns_error': re.compile(r'(DNS|nxdomain|host\s+not\s+found)', re.IGNORECASE),
        'redirect': re.compile(r'(redirect|30[1237])', re.IGNORECASE),
        'too_many_requests': re.compile(r'(429|rate\s+limit)', re.IGNORECASE),
    }

    def analyze_logs(self, log_content: str) -> List[HTTPIssue]:
        """分析日志中的 HTTP 请求问题"""
        issues = []
        lines = log_content.split('\n')

        for line in lines:
            line_lower = line.lower()

            # 检测状态码
            status_match = re.search(r'\b([45]\d{2})\b', line)
            if status_match:
                status = status_match.group(1)
                issue = self._analyze_status_code(status, line)
                if issue:
                    issues.append(issue)
                continue

            # 检测连接问题
            for issue_type, pattern in self.ISSUE_PATTERNS.items():
                if pattern.search(line):
                    issue = self._create_connection_issue(issue_type, line)
                    if issue:
                        issues.append(issue)
                    break

        return issues

    def analyze_code(self, filepath: str) -> List[HTTPIssue]:
        """分析代码中的 HTTP 请求问题"""
        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return []

        issues = []

        # 检测常见的 HTTP 请求问题
        # 检测缺少超时设置
        if re.search(r'requests\.(get|post)\([^)]*\)(?!\s*,\s*timeout)', content):
            if 'timeout' not in content:
                issues.append(HTTPIssue(
                    type='missing_timeout',
                    severity='medium',
                    url='N/A',
                    message='HTTP 请求缺少超时设置',
                    suggestion='添加 timeout 参数防止请求无限等待'
                ))

        # 检测缺少错误处理
        if re.search(r'response\s*=\s*requests\.(get|post)', content):
            if not re.search(r'except|if.*status_code', content):
                issues.append(HTTPIssue(
                    type='missing_error_handling',
                    severity='high',
                    url='N/A',
                    message='HTTP 请求缺少错误处理',
                    suggestion='添加 try-except 或检查响应状态码'
                ))

        # 检测使用不安全的 HTTP
        http_urls = re.findall(r'["\']http://[^"\']+["\']', content)
        for url in http_urls:
            issues.append(HTTPIssue(
                type='insecure_http',
                severity='low',
                url=url.strip('"\''),
                message='使用不安全的 HTTP 而非 HTTPS',
                suggestion='尽可能使用 HTTPS'
            ))

        return issues

    def _analyze_status_code(self, status: str, line: str) -> Optional[HTTPIssue]:
        """分析 HTTP 状态码"""
        if status.startswith('4'):
            category = 'client_error'
            severity = 'medium'
            desc = self.STATUS_CATEGORIES['4xx'].get(status, '客户端错误')
        elif status.startswith('5'):
            category = 'server_error'
            severity = 'high'
            desc = self.STATUS_CATEGORIES['5xx'].get(status, '服务器错误')
        else:
            return None

        return HTTPIssue(
            type=category,
            severity=severity,
            url=self._extract_url(line) or 'N/A',
            message=f'HTTP {status}: {desc}',
            suggestion=self._get_suggestion(status)
        )

    def _create_connection_issue(self, issue_type: str, line: str) -> Optional[HTTPIssue]:
        """创建连接问题"""
        suggestions = {
            'timeout': '检查服务响应时间，增加超时时间',
            'connection_refused': '检查服务是否运行，网络是否可达',
            'ssl_error': '检查 SSL 证书配置',
            'dns_error': '检查域名是否正确，DNS 配置',
            'redirect': '检查重定向逻辑',
            'too_many_requests': '实现请求限流，添加重试机制',
        }

        return HTTPIssue(
            type=issue_type,
            severity='high',
            url=self._extract_url(line) or 'N/A',
            message=line[:100],
            suggestion=suggestions.get(issue_type, '检查网络配置')
        )

    def _extract_url(self, text: str) -> Optional[str]:
        """提取 URL"""
        match = re.search(r'https?://[^\s"\']+', text)
        return match.group(0) if match else None

    def _get_suggestion(self, status: str) -> str:
        """获取状态码修复建议"""
        suggestions = {
            '400': '检查请求参数格式和内容',
            '401': '添加或刷新认证令牌',
            '403': '检查用户权限',
            '404': '检查 URL 路径是否正确',
            '429': '实现请求限流和重试',
            '500': '检查服务器日志',
            '502': '检查上游服务状态',
            '503': '服务暂时不可用，等待恢复',
            '504': '增加网关超时时间',
        }
        return suggestions.get(status, '查看具体错误信息')

    def format_report(self, issues: List[HTTPIssue]) -> str:
        """格式化报告"""
        if not issues:
            return "✅ 未发现 HTTP 问题"

        output = ["🌐 HTTP 问题分析", "=" * 50]

        # 按严重程度分组
        high = [i for i in issues if i.severity == 'high']
        medium = [i for i in issues if i.severity == 'medium']
        low = [i for i in issues if i.severity == 'low']

        if high:
            output.append(f"\n🔴 严重问题 ({len(high)}):")
            for i in high[:5]:
                output.append(f"  • {i.message}")
                output.append(f"    建议: {i.suggestion}")

        if medium:
            output.append(f"\n🟡 中等问题 ({len(medium)}):")
            for i in medium[:3]:
                output.append(f"  • {i.message}")

        if low:
            output.append(f"\n🟢 轻微问题 ({len(low)}):")
            for i in low[:2]:
                output.append(f"  • {i.message}")

        return "\n".join(output)


def analyze_http_logs(log_content: str) -> List[HTTPIssue]:
    """便捷函数"""
    analyzer = HTTPAnalyzer()
    return analyzer.analyze_logs(log_content)


def analyze_http_code(filepath: str) -> List[HTTPIssue]:
    """便捷函数"""
    analyzer = HTTPAnalyzer()
    return analyzer.analyze_code(filepath)
