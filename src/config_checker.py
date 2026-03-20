"""
配置问题检测器 - 检测配置文件错误
"""

import os
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ConfigIssue:
    """配置问题"""
    type: str  # syntax_error, missing_key, invalid_value, env_issue
    severity: str  # high, medium, low
    file: str
    message: str
    suggestion: str


class ConfigChecker:
    """配置问题检测器"""

    # 配置文件
    CONFIG_FILES = [
        '.env', '.env.local', '.env.development', '.env.production',
        'package.json', 'tsconfig.json', 'jsconfig.json',
        'pyproject.toml', 'setup.cfg', 'tox.ini',
        'docker-compose.yml', 'docker-compose.yaml',
        'nginx.conf', 'webpack.config.js', 'vite.config.js',
    ]

    # JSON 常见错误
    JSON_ERRORS = {
        'unexpected_token': 'JSON 语法错误',
        'missing_colon': '缺少冒号',
        'missing_quote': '缺少引号',
        'trailing_comma': '尾部逗号',
    }

    def check_file(self, filepath: str) -> List[ConfigIssue]:
        """检查配置文件"""
        if not os.path.exists(filepath):
            return []

        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.json':
            return self._check_json(filepath)
        elif ext in ['.yaml', '.yml']:
            return self._check_yaml(filepath)
        elif ext == '.toml':
            return self._check_toml(filepath)
        elif ext == '.env':
            return self._check_env(filepath)
        elif ext in ['.conf', '.ini']:
            return self._check_ini(filepath)

        return []

    def check_workspace(self, workspace: str = None) -> Dict[str, List[ConfigIssue]]:
        """检查工作区所有配置文件"""
        workspace = workspace or os.getcwd()
        results = {}

        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__', '.venv')]

            for file in files:
                filepath = os.path.join(root, file)

                # 检查是否是配置文件
                if file in self.CONFIG_FILES or file.startswith('.env'):
                    issues = self.check_file(filepath)
                    if issues:
                        results[filepath] = issues
                elif file.endswith(('.json', '.yaml', '.yml', '.toml', '.conf', '.ini')):
                    issues = self.check_file(filepath)
                    if issues:
                        results[filepath] = issues

        return results

    def _check_json(self, filepath: str) -> List[ConfigIssue]:
        """检查 JSON 文件"""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                json.loads(content)
        except json.JSONDecodeError as e:
            issues.append(ConfigIssue(
                type='syntax_error',
                severity='high',
                file=filepath,
                message=f'JSON 语法错误: {e.msg} at line {e.lineno}',
                suggestion=f'检查第 {e.lineno} 行的 {e.colno} 列附近'
            ))
        except Exception as e:
            issues.append(ConfigIssue(
                type='read_error',
                severity='high',
                file=filepath,
                message=f'读取文件失败: {str(e)}',
                suggestion='检查文件编码和权限'
            ))

        # 检查常见配置问题
        if os.path.basename(filepath) == 'package.json':
            issues.extend(self._check_package_json(filepath))

        return issues

    def _check_yaml(self, filepath: str) -> List[ConfigIssue]:
        """检查 YAML 文件"""
        issues = []

        try:
            import yaml
            with open(filepath, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except ImportError:
            # 无 yaml 库，跳过详细检查
            pass
        except yaml.YAMLError as e:
            issues.append(ConfigIssue(
                type='syntax_error',
                severity='high',
                file=filepath,
                message=f'YAML 语法错误: {str(e)}',
                suggestion='检查缩进和格式'
            ))
        except Exception as e:
            issues.append(ConfigIssue(
                type='read_error',
                severity='medium',
                file=filepath,
                message=f'读取失败: {str(e)}',
                suggestion='检查文件编码'
            ))

        return issues

    def _check_toml(self, filepath: str) -> List[ConfigIssue]:
        """检查 TOML 文件"""
        issues = []

        try:
            import tomli
            with open(filepath, 'rb') as f:
                tomli.load(f)
        except ImportError:
            try:
                import toml
                with open(filepath, 'r') as f:
                    toml.load(f)
            except ImportError:
                pass
        except Exception as e:
            issues.append(ConfigIssue(
                type='syntax_error',
                severity='high',
                file=filepath,
                message=f'TOML 语法错误: {str(e)}',
                suggestion='检查引号和等号格式'
            ))

        return issues

    def _check_env(self, filepath: str) -> List[ConfigIssue]:
        """检查 .env 文件"""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 检查格式
                if '=' not in line:
                    issues.append(ConfigIssue(
                        type='invalid_format',
                        severity='medium',
                        file=filepath,
                        message=f'第 {i} 行格式错误: 缺少 =',
                        suggestion='格式应为 KEY=value'
                    ))
                    continue

                key, value = line.split('=', 1)

                # 检查空值
                if not value.strip():
                    issues.append(ConfigIssue(
                        type='empty_value',
                        severity='low',
                        file=filepath,
                        message=f'第 {i} 行: {key} 值为空',
                        suggestion='如果需要空值使用空字符串 ""'
                    ))

                # 检查引号不匹配
                if value.count('"') % 2 != 0 or value.count("'") % 2 != 0:
                    issues.append(ConfigIssue(
                        type='unbalanced_quotes',
                        severity='medium',
                        file=filepath,
                        message=f'第 {i} 行: 引号不匹配',
                        suggestion='检查引号是否成对'
                    ))

        except Exception as e:
            issues.append(ConfigIssue(
                type='read_error',
                severity='high',
                file=filepath,
                message=f'读取失败: {str(e)}',
                suggestion='检查文件编码'
            ))

        return issues

    def _check_ini(self, filepath: str) -> List[ConfigIssue]:
        """检查 INI/CONF 文件"""
        issues = []

        try:
            import configparser
            parser = configparser.ConfigParser()
            parser.read(filepath, encoding='utf-8')
        except configparser.Error as e:
            issues.append(ConfigIssue(
                type='syntax_error',
                severity='high',
                file=filepath,
                message=f'INI 语法错误: {str(e)}',
                suggestion='检查节名称和键值对格式'
            ))
        except Exception as e:
            issues.append(ConfigIssue(
                type='read_error',
                severity='medium',
                file=filepath,
                message=f'读取失败: {str(e)}',
                suggestion='检查文件编码'
            ))

        return issues

    def _check_package_json(self, filepath: str) -> List[ConfigIssue]:
        """检查 package.json 特定问题"""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 检查 scripts
            if 'scripts' not in data:
                issues.append(ConfigIssue(
                    type='missing_key',
                    severity='low',
                    file=filepath,
                    message='缺少 scripts 字段',
                    suggestion='添加 scripts 以支持 npm scripts'
                ))

            # 检查 dependencies 和 devDependencies
            if 'dependencies' not in data and 'devDependencies' not in data:
                issues.append(ConfigIssue(
                    type='missing_key',
                    severity='medium',
                    file=filepath,
                    message='缺少依赖字段',
                    suggestion='添加 dependencies 或 devDependencies'
                ))

        except Exception:
            pass

        return issues

    def format_report(self, results: Dict[str, List[ConfigIssue]]) -> str:
        """格式化报告"""
        if not results:
            return "✅ 未发现配置问题"

        total = sum(len(issues) for issues in results.values())
        output = ["⚙️ 配置问题分析", "=" * 50, f"发现问题: {total} 个"]

        for filepath, issues in results.items():
            output.append(f"\n📄 {os.path.basename(filepath)}")
            for issue in issues[:5]:
                severity_icon = '🔴' if issue.severity == 'high' else '🟡' if issue.severity == 'medium' else '🟢'
                output.append(f"  {severity_icon} {issue.message}")
                if issue.suggestion:
                    output.append(f"     建议: {issue.suggestion}")

        return "\n".join(output)


def check_config_file(filepath: str) -> List[ConfigIssue]:
    """便捷函数"""
    checker = ConfigChecker()
    return checker.check_file(filepath)


def check_workspace_configs(workspace: str = None) -> Dict[str, List[ConfigIssue]]:
    """便捷函数"""
    checker = ConfigChecker()
    return checker.check_workspace(workspace)
