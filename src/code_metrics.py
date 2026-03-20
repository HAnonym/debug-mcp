"""
代码度量分析器 - 检测代码质量和复杂度
"""

import os
import re
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class Metric:
    """代码度量"""
    name: str
    value: float
    threshold: float
    status: str  # good, warning, bad


class CodeMetrics:
    """代码度量分析器"""

    def __init__(self):
        self.metrics = {}

    def analyze_file(self, filepath: str) -> Dict:
        """分析单个文件"""
        if not os.path.exists(filepath):
            return {}

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception:
            return {}

        ext = os.path.splitext(filepath)[1]
        result = {
            'file': filepath,
            'lines': len(lines),
            'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            'blank_lines': len([l for l in lines if not l.strip()]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#') or l.strip().startswith('//')]),
        }

        # 文件类型特定分析
        if ext == '.py':
            result.update(self._analyze_python(content, lines))
        elif ext in ['.js', '.ts']:
            result.update(self._analyze_js(content, lines))

        return result

    def _analyze_python(self, content: str, lines: List[str]) -> Dict:
        """分析 Python 代码"""
        # 函数/类数量
        functions = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))
        classes = len(re.findall(r'^class\s+\w+', content, re.MULTILINE))

        # 计算圈复杂度 (简化版)
        complexity = 1
        complexity += len(re.findall(r'\bif\b', content))
        complexity += len(re.findall(r'\bfor\b', content))
        complexity += len(re.findall(r'\bwhile\b', content))
        complexity += len(re.findall(r'\band\b', content))
        complexity += len(re.findall(r'\bor\b', content))

        # 检测重复代码 (简化)
        duplicates = self._find_duplicates(lines)

        return {
            'functions': functions,
            'classes': classes,
            'complexity': complexity,
            'duplicates': duplicates,
        }

    def _analyze_js(self, content: str, lines: List[str]) -> Dict:
        """分析 JavaScript 代码"""
        functions = len(re.findall(r'function\s+\w+', content))
        arrow_funcs = len(re.findall(r'=>', content))
        classes = len(re.findall(r'class\s+\w+', content))

        # 圈复杂度
        complexity = 1
        complexity += len(re.findall(r'\bif\b', content))
        complexity += len(re.findall(r'\bfor\b', content))
        complexity += len(re.findall(r'\bwhile\b', content))
        complexity += len(re.findall(r'\?\?', content))  # nullish coalescing

        duplicates = self._find_duplicates(lines)

        return {
            'functions': functions,
            'arrow_functions': arrow_funcs,
            'classes': classes,
            'complexity': complexity,
            'duplicates': duplicates,
        }

    def _find_duplicates(self, lines: List[str]) -> int:
        """查找重复代码行 (简化)"""
        code_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 20]
        if len(code_lines) < 3:
            return 0

        duplicates = 0
        seen = {}
        for line in code_lines:
            if line in seen:
                duplicates += 1
            else:
                seen[line] = True

        return duplicates

    def analyze_workspace(self, workspace: str = None) -> Dict:
        """分析整个工作区"""
        workspace = workspace or os.getcwd()
        results = []
        total_lines = 0
        total_complexity = 0

        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in
                      ('.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build')]

            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.vue', '.jsx', '.tsx')):
                    filepath = os.path.join(root, file)
                    metrics = self.analyze_file(filepath)
                    if metrics:
                        results.append(metrics)
                        total_lines += metrics.get('code_lines', 0)
                        total_complexity += metrics.get('complexity', 0)

        # 计算平均复杂度
        avg_complexity = total_complexity / len(results) if results else 0

        return {
            'files': len(results),
            'total_lines': total_lines,
            'avg_complexity': avg_complexity,
            'details': results,
            'issues': self._find_issues(results)
        }

    def _find_issues(self, results: List[Dict]) -> List[Dict]:
        """发现问题"""
        issues = []

        for r in results:
            # 复杂度过高
            if r.get('complexity', 0) > 20:
                issues.append({
                    'type': 'high_complexity',
                    'file': r['file'],
                    'value': r['complexity'],
                    'message': f"圈复杂度过高: {r['complexity']}"
                })

            # 重复代码
            if r.get('duplicates', 0) > 5:
                issues.append({
                    'type': 'duplicates',
                    'file': r['file'],
                    'value': r['duplicates'],
                    'message': f"存在重复代码: {r['duplicates']} 处"
                })

            # 文件过大
            if r.get('lines', 0) > 500:
                issues.append({
                    'type': 'large_file',
                    'file': r['file'],
                    'value': r['lines'],
                    'message': f"文件过大: {r['lines']} 行"
                })

        return issues

    def format_report(self, result: Dict) -> str:
        """格式化报告"""
        output = []

        output.append("📊 代码度量报告")
        output.append("=" * 50)
        output.append(f"文件数: {result['files']}")
        output.append(f"代码行: {result['total_lines']}")
        output.append(f"平均复杂度: {result['avg_complexity']:.1f}")
        output.append("")

        if result['issues']:
            output.append("⚠️ 发现问题:")
            for issue in result['issues'][:10]:
                output.append(f"  • {issue['message']}")
                output.append(f"    {issue['file']}")
        else:
            output.append("✅ 代码质量良好")

        return "\n".join(output)


def analyze_metrics(workspace: str = None) -> Dict:
    """便捷函数"""
    analyzer = CodeMetrics()
    return analyzer.analyze_workspace(workspace or os.getcwd())
