"""
测试运行器 - 自动检测和运行测试
"""

import os
import subprocess
import json
from typing import Dict, List, Optional
from pathlib import Path

from .logger import get_logger

logger = get_logger("debug-mcp.test_runner")


class TestRunner:
    """测试运行器"""

    # 支持的测试框架
    FRAMEWORKS = {
        'pytest': {
            'files': ['test_*.py', '*_test.py', 'tests/'],
            'cmd': ['pytest', '-v'],
            'lang': 'python'
        },
        'unittest': {
            'files': ['test_*.py'],
            'cmd': ['python', '-m', 'unittest'],
            'lang': 'python'
        },
        'jest': {
            'files': ['*.test.js', '*.spec.js', '__tests__/'],
            'cmd': ['npx', 'jest'],
            'lang': 'javascript'
        },
        'vitest': {
            'files': ['*.test.js', '*.spec.js'],
            'cmd': ['npx', 'vitest'],
            'lang': 'javascript'
        },
        'mocha': {
            'files': ['test/*.js', '*.test.js'],
            'cmd': ['npx', 'mocha'],
            'lang': 'javascript'
        },
        'go test': {
            'files': ['*_test.go'],
            'cmd': ['go', 'test', '-v'],
            'lang': 'go'
        },
        'cargo test': {
            'files': ['tests/', 'src/*/'],
            'cmd': ['cargo', 'test', '--', '--nocapture'],
            'lang': 'rust'
        },
        'npm test': {
            'files': ['package.json'],
            'cmd': ['npm', 'test'],
            'lang': 'javascript'
        }
    }

    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.getcwd()
        self.detected_framework = None

    def detect_framework(self) -> Optional[str]:
        """检测项目使用的测试框架"""
        logger.info(f"Detecting test framework in: {self.workspace}")

        for framework, config in self.FRAMEWORKS.items():
            for pattern in config['files']:
                # 检查文件/目录是否存在
                if '*' in pattern:
                    # 通配符模式
                    import glob
                    matches = glob.glob(os.path.join(self.workspace, pattern.replace('*', '*')))
                    if matches:
                        self.detected_framework = framework
                        logger.info(f"Detected framework: {framework}")
                        return framework
                else:
                    # 精确匹配
                    path = os.path.join(self.workspace, pattern)
                    if os.path.exists(path):
                        self.detected_framework = framework
                        logger.info(f"Detected framework: {framework}")
                        return framework

        # 检查 package.json 中的测试脚本
        package_json = os.path.join(self.workspace, 'package.json')
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    pkg = json.load(f)
                    scripts = pkg.get('scripts', {})
                    if 'test' in scripts:
                        self.detected_framework = 'npm test'
                        logger.info("Detected framework: npm test")
                        return 'npm test'
            except Exception:
                pass

        # 检查 go.mod
        go_mod = os.path.join(self.workspace, 'go.mod')
        if os.path.exists(go_mod):
            self.detected_framework = 'go test'
            logger.info("Detected framework: go test")
            return 'go test'

        # 检查 Cargo.toml
        cargo_toml = os.path.join(self.workspace, 'Cargo.toml')
        if os.path.exists(cargo_toml):
            self.detected_framework = 'cargo test'
            logger.info("Detected framework: cargo test")
            return 'cargo test'

        logger.warning("No test framework detected")
        return None

    def run_tests(self, pattern: str = None, verbose: bool = True) -> Dict:
        """
        运行测试

        Args:
            pattern: 测试文件/函数匹配模式
            verbose: 是否详细输出

        Returns:
            测试结果字典
        """
        if not self.detected_framework:
            self.detect_framework()

        if not self.detected_framework:
            return {
                'success': False,
                'error': 'No test framework detected',
                'output': ''
            }

        framework = self.FRAMEWORKS.get(self.detected_framework)
        if not framework:
            return {
                'success': False,
                'error': f'Unknown framework: {self.detected_framework}',
                'output': ''
            }

        cmd = framework['cmd'].copy()

        # 添加模式过滤
        if pattern:
            if self.detected_framework == 'pytest':
                cmd.extend(['-k', pattern])
            elif self.detected_framework in ['jest', 'vitest', 'mocha']:
                cmd.extend(['--testNamePattern', pattern])
            elif self.detected_framework == 'go test':
                cmd.extend(['-run', pattern])

        # 添加详细输出
        if verbose and self.detected_framework == 'pytest':
            cmd.append('-v')

        logger.info(f"Running tests: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )

            success = result.returncode == 0

            return {
                'success': success,
                'returncode': result.returncode,
                'output': result.stdout + result.stderr,
                'framework': self.detected_framework,
                'cmd': ' '.join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test timeout (2 minutes)',
                'output': '',
                'framework': self.detected_framework
            }
        except Exception as e:
            logger.error(f"Test runner error: {e}")
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'framework': self.detected_framework
            }

    def run_related_tests(self, error_context: str) -> Dict:
        """
        根据错误上下文运行相关测试

        Args:
            error_context: 错误信息或相关代码

        Returns:
            测试结果
        """
        # 尝试从错误中提取关键词
        keywords = []

        # 提取函数名
        import re
        func_matches = re.findall(r'def (\w+)|function (\w+)', error_context)
        for match in func_matches:
            keywords.extend([m for m in match if m])

        # 提取文件名
        file_matches = re.findall(r'([a-zA-Z_]+\.py|[a-zA-Z_]+\.js)', error_context)
        keywords.extend(file_matches)

        if keywords:
            # 尝试运行包含关键词的测试
            for keyword in keywords[:3]:
                result = self.run_tests(pattern=keyword, verbose=False)
                if result.get('output'):
                    return result

        # 如果没有匹配，返回总体测试结果
        return self.run_tests()

    def get_test_info(self) -> Dict:
        """获取测试环境信息"""
        info = {
            'workspace': self.workspace,
            'framework': self.detected_framework,
            'available': []
        }

        # 检查可用的测试框架
        for framework, config in self.FRAMEWORKS.items():
            for pattern in config['files']:
                path = os.path.join(self.workspace, pattern.replace('*', '*'))
                if os.path.exists(path):
                    info['available'].append(framework)
                    break

        return info


def run_tests(workspace: str = None, pattern: str = None) -> Dict:
    """便捷函数：运行测试"""
    runner = TestRunner(workspace)
    return runner.run_tests(pattern)


def get_test_info(workspace: str = None) -> Dict:
    """便捷函数：获取测试信息"""
    runner = TestRunner(workspace)
    runner.detect_framework()
    return runner.get_test_info()
