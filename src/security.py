"""
安全扫描器 - 识别常见安全漏洞
"""

import re
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SecurityIssue:
    """安全问题"""
    type: str  # sql_injection, xss, etc.
    severity: str  # critical, high, medium, low
    file: str
    line: int
    code: str
    description: str
    suggestion: str


class SecurityScanner:
    """安全扫描器"""

    # 安全问题模式
    PATTERNS = {
        # SQL 注入
        'sql_injection': {
            'patterns': [
                (r'execute\([^)]*\%s[^)]*\)', 'execute with %s'),
                (r'cursor\.execute\([^)]*f["\'].*SELECT', 'f-string in SQL'),
                (r'"\s*\+\s*sql\s*\+"', 'string concatenation in SQL'),
                (r'\.format\([^)]*sql', '.format() in SQL query'),
            ],
            'description': 'SQL 注入漏洞',
            'severity': 'critical',
            'suggestion': '使用参数化查询或 ORM'
        },
        # 命令注入
        'command_injection': {
            'patterns': [
                (r'os\.system\([^)]*\%', 'os.system with % formatting'),
                (r'subprocess\.call\([^)]*shell=True', 'subprocess with shell=True'),
                (r'eval\([^)]*request', 'eval on user input'),
                (r'exec\([^)]*request', 'exec on user input'),
            ],
            'description': '命令注入漏洞',
            'severity': 'critical',
            'suggestion': '避免使用 shell=True，使用参数列表'
        },
        # 硬编码密钥
        'hardcoded_secret': {
            'patterns': [
                (r'["\']api[_-]?key["\']\s*[:=]\s*["\'][^"\']{20,}', '硬编码 API Key'),
                (r'["\']secret["\']\s*[:=]\s*["\'][^"\']{20,}', '硬编码密钥'),
                (r'["\']password["\']\s*[:=]\s*["\'][^"\']+', '硬编码密码'),
                (r'["\']token["\']\s*[:=]\s*["\'][^"\']{20,}', '硬编码 Token'),
                (r'Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', '硬编码 JWT'),
                (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Token'),
                (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
            ],
            'description': '硬编码敏感信息',
            'severity': 'high',
            'suggestion': '使用环境变量或密钥管理服务'
        },
        # XSS 漏洞
        'xss': {
            'patterns': [
                (r'innerHTML\s*=', 'innerHTML 赋值'),
                (r'dangerouslySetInnerHTML', 'React dangerouslySetInnerHTML'),
                (r'\{__html:', 'React __html'),
                (r'response\.write\([^)]*request', '直接响应用户输入'),
            ],
            'description': '跨站脚本 (XSS) 漏洞',
            'severity': 'high',
            'suggestion': '使用文本转义或内容安全策略'
        },
        # 不安全的随机数
        'insecure_random': {
            'patterns': [
                (r'random\.random\(\)', '使用 random.random()'),
                (r'Math\.random\(', '使用 Math.random()'),
            ],
            'description': '不安全的随机数',
            'severity': 'medium',
            'suggestion': '使用 secrets 模块或 crypto.randomBytes'
        },
        # 不安全的 SSL
        'insecure_ssl': {
            'patterns': [
                (r'verify\s*=\s*False', 'SSL 验证关闭'),
                (r'ssl\.VERIFY_NONE', 'SSL 验证关闭'),
                (r'--no-check-certificate', '不检查证书'),
            ],
            'description': '不安全的 SSL 配置',
            'severity': 'high',
            'suggestion': '启用 SSL 证书验证'
        },
        # 路径遍历
        'path_traversal': {
            'patterns': [
                (r'open\([^)]*\+[^)]*request', '用户输入拼接文件路径'),
                (r'os\.path\.join\([^)]*request', '用户输入加入路径'),
            ],
            'description': '路径遍历漏洞',
            'severity': 'high',
            'suggestion': '验证和规范化文件路径'
        },
        # 不安全的反序列化
        'insecure_deserialize': {
            'patterns': [
                (r'pickle\.load\(', 'pickle 反序列化'),
                (r'yaml\.load\([^,)]*\)', 'yaml 不安全加载'),
                (r'JSON\.parse\([^)]*eval', 'eval 解析 JSON'),
            ],
            'description': '不安全的反序列化',
            'severity': 'critical',
            'suggestion': '使用安全的序列化方法，如 json'
        },
        # 弱加密
        'weak_crypto': {
            'patterns': [
                (r'md5\(', '使用 MD5'),
                (r'sha1\(', '使用 SHA1'),
                (r'DES\.new\(', '使用 DES'),
                (r'Crypto\.Cipher\.DES', '使用 DES'),
            ],
            'description': '弱加密算法',
            'severity': 'medium',
            'suggestion': '使用 AES-256 或更强的加密算法'
        },
        # 权限问题
        'permission_issue': {
            'patterns': [
                (r'chmod\s+777', 'chmod 777'),
                (r'0o777', '八进制 777 权限'),
                (r'allow_permissions\s*=\s*["\']\*', '通配符权限'),
            ],
            'description': '过度的文件权限',
            'severity': 'medium',
            'suggestion': '使用最小权限原则'
        },
    }

    def scan_file(self, filepath: str) -> List[SecurityIssue]:
        """扫描单个文件"""
        issues = []

        if not os.path.exists(filepath):
            return issues

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return issues

        content = ''.join(lines)

        # 检测各种模式
        for issue_type, config in self.PATTERNS.items():
            for pattern, code_desc in config['patterns']:
                try:
                    for match in re.finditer(pattern, content, re.IGNORECASE):
                        # 计算行号
                        line_num = content[:match.start()].count('\n') + 1

                        # 获取代码行
                        code_line = lines[line_num - 1].strip() if line_num <= len(lines) else ''

                        issues.append(SecurityIssue(
                            type=issue_type,
                            severity=config['severity'],
                            file=filepath,
                            line=line_num,
                            code=code_line[:100],
                            description=config['description'],
                            suggestion=config['suggestion']
                        ))
                except re.error:
                    continue

        return issues

    def scan_workspace(self, workspace: str = None) -> Dict:
        """扫描整个工作区"""
        issues = []
        files_scanned = 0

        workspace = workspace or os.getcwd()

        for root, dirs, files in os.walk(workspace):
            # 排除目录
            dirs[:] = [d for d in dirs if d not in
                      ('.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build')]

            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.go')):
                    filepath = os.path.join(root, file)
                    file_issues = self.scan_file(filepath)
                    issues.extend(file_issues)
                    files_scanned += 1

        # 按严重程度分组
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
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

        critical = len(by_severity['critical'])
        high = len(by_severity['high'])
        medium = len(by_severity['medium'])
        low = len(by_severity['low'])

        if critical > 0:
            summary.append(f"🚨 严重: {critical} 个漏洞需要立即修复!")
        if high > 0:
            summary.append(f"🔴 高危: {high} 个问题需要尽快处理")
        if medium > 0:
            summary.append(f"🟡 中危: {medium} 个问题建议优化")
        if low > 0:
            summary.append(f"🟢 低危: {low} 个问题可后续处理")

        if not summary:
            summary.append("✅ 未发现明显安全问题")

        return summary

    def format_report(self, result: Dict) -> str:
        """格式化报告"""
        output = []

        output.append("🔒 安全扫描报告")
        output.append("=" * 50)
        output.append(f"扫描文件: {result['files_scanned']}")
        output.append(f"发现问题: {result['total_issues']}")
        output.append("")

        # 摘要
        output.append("📈 摘要:")
        for line in result['summary']:
            output.append(f"  {line}")
        output.append("")

        # 严重问题
        for severity in ['critical', 'high', 'medium']:
            issues = result['by_severity'].get(severity, [])
            if issues:
                icon = '🚨' if severity == 'critical' else '🔴'
                output.append(f"{icon} {severity.upper()} 严重问题:")
                for issue in issues[:5]:
                    output.append(f"  • {issue.description}")
                    output.append(f"    文件: {issue.file}:{issue.line}")
                    output.append(f"    代码: {issue.code[:60]}")
                    output.append(f"    建议: {issue.suggestion}")
                output.append("")

        return "\n".join(output)


def scan_security(workspace: str = None) -> Dict:
    """便捷函数：安全扫描"""
    scanner = SecurityScanner()
    return scanner.scan_workspace(workspace or os.getcwd())


def format_security_report(result: Dict) -> str:
    """便捷函数：格式化安全报告"""
    scanner = SecurityScanner()
    return scanner.format_report(result)
