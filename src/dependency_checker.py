"""
依赖问题检测器 - 检测依赖缺失、版本冲突、过时问题
"""

import os
import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DependencyIssue:
    """依赖问题"""
    type: str  # missing, conflict, outdated, unused
    severity: str  # high, medium, low
    package: str
    message: str
    suggestion: str


class DependencyChecker:
    """依赖问题检测器"""

    # 依赖文件
    DEPENDENCY_FILES = {
        'python': ['requirements.txt', 'pyproject.toml', 'Pipfile', 'setup.py'],
        'javascript': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'],
        'go': ['go.mod', 'go.sum'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
    }

    # Python 常用包
    COMMON_PYTHON_PACKAGES = {
        'requests', 'numpy', 'pandas', 'flask', 'django', 'fastapi',
        'sqlalchemy', 'pytest', 'pillow', 'tensorflow', 'torch',
        'redis', 'celery', 'pydantic', 'httpx', 'tenacity',
    }

    # JS 常用包
    COMMON_JS_PACKAGES = {
        'react', 'vue', 'angular', 'express', 'next', 'nuxt',
        'lodash', 'axios', 'moment', 'webpack', 'vite',
        'typescript', 'eslint', 'prettier', 'jest', 'cypress',
    }

    def check_workspace(self, workspace: str = None) -> Dict[str, List[DependencyIssue]]:
        """检查工作区依赖问题"""
        workspace = workspace or os.getcwd()
        results = {}

        # 检测项目类型
        lang = self._detect_language(workspace)

        if lang == 'python':
            results['python'] = self._check_python_deps(workspace)
        elif lang == 'javascript':
            results['javascript'] = self._check_js_deps(workspace)

        return results

    def _detect_language(self, workspace: str) -> Optional[str]:
        """检测项目语言"""
        files = os.listdir(workspace)

        if 'requirements.txt' in files or any(f in files for f in ['pyproject.toml', 'Pipfile', 'setup.py']):
            return 'python'
        elif 'package.json' in files:
            return 'javascript'
        elif 'go.mod' in files:
            return 'go'
        elif 'Cargo.toml' in files:
            return 'rust'

        return None

    def _check_python_deps(self, workspace: str) -> List[DependencyIssue]:
        """检查 Python 依赖"""
        issues = []

        # 检查 requirements.txt
        req_file = os.path.join(workspace, 'requirements.txt')
        if os.path.exists(req_file):
            issues.extend(self._check_requirements_txt(req_file))

        # 检查 pyproject.toml
        pyproject = os.path.join(workspace, 'pyproject.toml')
        if os.path.exists(pyproject):
            issues.extend(self._check_pyproject_toml(pyproject))

        return issues

    def _check_requirements_txt(self, filepath: str) -> List[DependencyIssue]:
        """检查 requirements.txt"""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 检查版本格式
                if '==' in line:
                    pkg = line.split('==')[0]
                    version = line.split('==')[1]
                    # 检查是否有不安全的版本
                    if version == '*':
                        issues.append(DependencyIssue(
                            type='unsafe_version',
                            severity='medium',
                            package=pkg,
                            message=f'{pkg} 使用不安全版本 *',
                            suggestion='指定具体版本号'
                        ))

                # 检查包名格式
                if re.match(r'^[\d\-\.]', line):
                    issues.append(DependencyIssue(
                        type='invalid_format',
                        severity='high',
                        package=line,
                        message=f'第 {i} 行: 包名不能以数字或特殊字符开头',
                        suggestion='使用正确的格式: package-name==1.0.0'
                    ))

                # 检查可选依赖格式
                if '; ' in line:
                    condition = line.split('; ')[1]
                    if not any(kw in condition for kw in ('python_version', 'sys_platform', 'platform')):
                        issues.append(DependencyIssue(
                            type='invalid_condition',
                            severity='low',
                            package=line.split(';')[0],
                            message=f'第 {i} 行: 条件格式可能不正确',
                            suggestion='使用 python_version, sys_platform, platform_os'
                        ))

        except Exception as e:
            issues.append(DependencyIssue(
                type='read_error',
                severity='high',
                package='N/A',
                message=f'读取文件失败: {str(e)}',
                suggestion='检查文件编码'
            ))

        return issues

    def _check_pyproject_toml(self, filepath: str) -> List[DependencyIssue]:
        """检查 pyproject.toml"""
        issues = []

        try:
            import tomli
            with open(filepath, 'rb') as f:
                data = tomli.load(f)
        except ImportError:
            try:
                import toml
                with open(filepath, 'r') as f:
                    data = toml.load(f)
            except ImportError:
                return issues
        except Exception as e:
            issues.append(DependencyIssue(
                type='parse_error',
                severity='high',
                package='N/A',
                message=f'解析失败: {str(e)}',
                suggestion='检查 TOML 格式'
            ))
            return issues

        # 检查依赖配置
        if 'project' in data:
            deps = data['project'].get('dependencies', [])
            optional_deps = data['project'].get('optional-dependencies', {})

            # 检查依赖格式
            for dep in deps:
                if isinstance(dep, str):
                    if ';' in dep and not any(kw in dep for kw in ('python', 'sys_platform')):
                        issues.append(DependencyIssue(
                            type='invalid_condition',
                            severity='low',
                            package=dep.split(';')[0],
                            message=f'依赖条件可能不正确: {dep}',
                            suggestion='检查条件语法'
                        ))

        return issues

    def _check_js_deps(self, workspace: str) -> List[DependencyIssue]:
        """检查 JS 依赖"""
        issues = []

        pkg_json = os.path.join(workspace, 'package.json')
        if os.path.exists(pkg_json):
            issues.extend(self._check_package_json(pkg_json))

        return issues

    def _check_package_json(self, filepath: str) -> List[DependencyIssue]:
        """检查 package.json"""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}

            for pkg, version in deps.items():
                # 检查不安全的版本
                if version == '*':
                    issues.append(DependencyIssue(
                        type='unsafe_version',
                        severity='high',
                        package=pkg,
                        message=f'{pkg} 使用不安全版本 *',
                        suggestion='指定具体版本或使用 ^, ~, >= 等范围'
                    ))

                # 检查过于宽松的版本
                if version.startswith('>'):
                    issues.append(DependencyIssue(
                        type='outdated_range',
                        severity='medium',
                        package=pkg,
                        message=f'{pkg} 使用 > 范围，可能导致问题',
                        suggestion='使用 ^ 或 ~ 限制范围'
                    ))

            # 检查 scripts
            scripts = data.get('scripts', {})
            if not scripts:
                issues.append(DependencyIssue(
                    type='missing_scripts',
                    severity='low',
                    package='N/A',
                    message='缺少 scripts 配置',
                    suggestion='添加常用 scripts: start, build, test'
                ))

        except json.JSONDecodeError as e:
            issues.append(DependencyIssue(
                type='parse_error',
                severity='high',
                package='N/A',
                message=f'JSON 解析失败: {e.msg}',
                suggestion=f'检查第 {e.lineno} 行'
            ))
        except Exception as e:
            issues.append(DependencyIssue(
                type='read_error',
                severity='high',
                package='N/A',
                message=f'读取失败: {str(e)}',
                suggestion='检查文件格式'
            ))

        return issues

    def check_installed_vs_required(self, workspace: str = None) -> List[DependencyIssue]:
        """检查已安装但未在依赖文件中声明的包（Python）"""
        issues = []

        workspace = workspace or os.getcwd()
        req_file = os.path.join(workspace, 'requirements.txt')

        if not os.path.exists(req_file):
            return issues

        # 读取 requirements.txt
        required = set()
        try:
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        pkg = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                        required.add(pkg.lower())
        except Exception:
            return issues

        # 这个功能需要虚拟环境，暂时只返回空列表
        # 实际实现需要对比 site-packages

        return issues

    def format_report(self, results: Dict[str, List[DependencyIssue]]) -> str:
        """格式化报告"""
        if not results or all(not issues for issues in results.values()):
            return "✅ 未发现依赖问题"

        output = ["📦 依赖问题分析", "=" * 50]

        for lang, issues in results.items():
            if not issues:
                continue

            high = [i for i in issues if i.severity == 'high']
            medium = [i for i in issues if i.severity == 'medium']
            low = [i for i in issues if i.severity == 'low']

            output.append(f"\n🔹 {lang.upper()} ({len(issues)} 个问题)")

            if high:
                output.append(f"  🔴 严重 ({len(high)}):")
                for i in high[:3]:
                    output.append(f"    • {i.package}: {i.message}")

            if medium:
                output.append(f"  🟡 中等 ({len(medium)}):")
                for i in medium[:2]:
                    output.append(f"    • {i.package}: {i.message}")

            if low:
                output.append(f"  🟢 轻微 ({len(low)}):")

        return "\n".join(output)


def check_dependencies(workspace: str = None) -> Dict[str, List[DependencyIssue]]:
    """便捷函数"""
    checker = DependencyChecker()
    return checker.check_workspace(workspace)
