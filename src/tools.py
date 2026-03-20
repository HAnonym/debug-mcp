"""
工具集 - 调试 Agent 可用的工具（优化版）
- 添加 LRU 缓存
- 支持更多编程语言
- 改进错误处理
"""

import os
import re
import threading
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

from .logger import get_logger

logger = get_logger("debug-mcp.tools")


# 排除目录
DEFAULT_EXCLUDE_DIRS = ('.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode', 'dist', 'build', '.tox')

# 支持的文件扩展名
SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.vue', '.jsx', '.tsx', '.go', '.java', '.rs', '.php', '.cs', '.rb', '.swift', '.kt', '.scala', '.c', '.cpp', '.h', '.hpp')


class FileIndex:
    """文件索引（带缓存和增量更新）"""

    def __init__(self, workspace: str):
        self.workspace = workspace
        self._index: Dict[str, List[str]] = {}  # extension -> [filepath, ...]
        self._lock = threading.RLock()
        self._last_scan_time = 0.0

    def scan_workspace(self, force: bool = False) -> Dict[str, List[str]]:
        """扫描工作区建立索引"""
        with self._lock:
            import time

            # 如果有缓存且不是强制刷新，直接返回
            if self._index and not force and (time.time() - self._last_scan_time) < 60:  # 1分钟内不重新扫描
                return self._index

            logger.info(f"Scanning workspace: {self.workspace}")

            new_index: Dict[str, List[str]] = {}

            for root, dirs, files in os.walk(self.workspace):
                # 排除目录
                dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDE_DIRS]

                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        filepath = os.path.join(root, file)
                        if ext not in new_index:
                            new_index[ext] = []
                        new_index[ext].append(filepath)

            self._index = new_index
            self._last_scan_time = time.time()

            total_files = sum(len(v) for v in new_index.values())
            logger.info(f"Indexed {total_files} files in {len(new_index)} categories")

            return self._index

    def search_by_keyword(self, keyword: str, extensions: Optional[tuple] = None) -> List[str]:
        """搜索包含关键词的文件"""
        self.scan_workspace()

        if extensions is None:
            extensions = SUPPORTED_EXTENSIONS

        results = []
        keyword_lower = keyword.lower()

        for ext, files in self._index.items():
            if ext not in extensions:
                continue

            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        if keyword_lower in content:
                            results.append(filepath)
                except Exception:
                    pass

        return results

    def get_all_files(self, extensions: Optional[tuple] = None) -> List[str]:
        """获取所有文件"""
        self.scan_workspace()

        if extensions is None:
            extensions = SUPPORTED_EXTENSIONS

        results = []
        for ext, files in self._index.items():
            if ext in extensions:
                results.extend(files)

        return results


class Tools:
    """工具集（优化版）"""

    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.getcwd()
        self._tools: Dict[str, Callable] = {}
        self._file_index = FileIndex(self.workspace)
        self._register_tools()
        logger.info(f"Tools initialized for workspace: {self.workspace}")

    def _register_tools(self):
        self._tools = {
            'search_code': self.search_code,
            'read_file': self.read_file,
            'list_files': self.list_files,
            'grep': self.grep,
            'search_error_pattern': self.search_error_pattern,
            'check_syntax': self.check_syntax,
            'find_similar_code': self.find_similar_code,
            'get_file_info': self.get_file_info,
        }

    def get_tools(self) -> Dict[str, Callable]:
        return self._tools

    def get_tools_description(self) -> str:
        descriptions = []
        for name, func in self._tools.items():
            doc = func.__doc__ or "无描述"
            descriptions.append(f"- {name}: {doc.strip()}")
        return "\n".join(descriptions)

    def refresh_index(self, force: bool = False):
        """刷新文件索引"""
        self._file_index.scan_workspace(force=force)

    def search_code(self, keyword: str, file_pattern: str = "*", limit: int = 50) -> str:
        """搜索代码文件"""
        try:
            results = self._file_index.search_by_keyword(keyword)

            if results:
                output = f"找到 {len(results)} 个文件:\n"
                for filepath in results[:limit]:
                    output += f"  {filepath}\n"

                if len(results) > limit:
                    output += f"\n... 还有 {len(results) - limit} 个文件"

                return output
            return f"未找到包含 '{keyword}' 的文件"
        except Exception as e:
            logger.error(f"search_code failed: {e}")
            return f"搜索失败: {str(e)}"

    def read_file(self, filepath: str, lines: int = 100, offset: int = 0) -> str:
        """读取文件内容"""
        try:
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.workspace, filepath)

            if not os.path.exists(filepath):
                return f"文件不存在: {filepath}"

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.readlines()

                total_lines = len(content)
                lines = min(lines, total_lines - offset)
                selected = content[offset:offset + lines]

                result = f"文件: {filepath}\n"
                result += f"总行数: {total_lines}, 显示: {offset + 1}-{offset + lines}\n"
                result += "-" * 60 + "\n"
                result += "".join(selected)

                return result
            except IOError as e:
                return f"读取文件失败: {str(e)}"
        except Exception as e:
            logger.error(f"read_file failed: {e}")
            return f"读取失败: {str(e)}"

    def list_files(self, pattern: str = "*", recursive: bool = False, limit: int = 100) -> str:
        """列出匹配的文件"""
        try:
            import glob

            if recursive:
                search_pattern = os.path.join(self.workspace, "**", pattern)
            else:
                search_pattern = os.path.join(self.workspace, pattern)

            results = []
            for filepath in glob.glob(search_pattern, recursive=recursive):
                if os.path.isfile(filepath):
                    results.append(filepath)

            if results:
                output = f"找到 {len(results)} 个文件:\n"
                for f in results[:limit]:
                    output += f"  {f}\n"

                if len(results) > limit:
                    output += f"\n... 还有 {len(results) - limit} 个文件"

                return output
            return f"未找到匹配 '{pattern}' 的文件"
        except Exception as e:
            logger.error(f"list_files failed: {e}")
            return f"列出文件失败: {str(e)}"

    def grep(self, pattern: str, path: str = None, context: int = 2, limit: int = 50) -> str:
        """
        正则搜索

        Args:
            pattern: 正则表达式
            path: 搜索路径
            context: 上下文行数
            limit: 结果数量限制
        """
        path = path or self.workspace
        results = []

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return f"无效的正则表达式: {e}"

        try:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDE_DIRS]

                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        continue

                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines, 1):
                                if regex.search(line):
                                    # 添加上下文
                                    start = max(0, i - context - 1)
                                    end = min(len(lines), i + context)

                                    result_lines = []
                                    for j in range(start, end):
                                        prefix = ">>> " if j == i - 1 else "    "
                                        result_lines.append(f"{prefix}{j + 1}: {lines[j].rstrip()}")

                                    results.append({
                                        'file': filepath,
                                        'line': i,
                                        'content': result_lines
                                    })
                    except Exception:
                        pass

            if results:
                output = f"找到 {len(results)} 处匹配:\n"
                for r in results[:limit]:
                    output += f"\n{r['file']}:{r['line']}\n"
                    output += "\n".join(r['content']) + "\n"

                if len(results) > limit:
                    output += f"\n... 还有 {len(results) - limit} 处匹配"

                return output
            return f"未找到匹配 '{pattern}' 的内容"
        except Exception as e:
            logger.error(f"grep failed: {e}")
            return f"搜索失败: {str(e)}"

    def search_error_pattern(self, error_type: str) -> Dict:
        """搜索错误模式"""
        patterns = {
            'typeerror': {
                'name': 'TypeError',
                'keywords': ['TypeError', 'is not', 'undefined', 'null', 'cannot read'],
                'solutions': [
                    '检查变量是否已定义',
                    '检查 API 返回值是否为 null/undefined',
                    '使用 optional chaining (?.) 或空值合并 (??)',
                ]
            },
            'syntaxerror': {
                'name': 'SyntaxError',
                'keywords': ['SyntaxError', 'unexpected token', 'parse error'],
                'solutions': [
                    '检查括号、引号是否匹配',
                    '检查逗号、分号是否正确',
                    '检查是否有语法错误',
                ]
            },
            'referenceerror': {
                'name': 'ReferenceError',
                'keywords': ['ReferenceError', 'is not defined', 'not found'],
                'solutions': [
                    '检查变量/函数是否已声明',
                    '检查导入是否正确',
                    '检查作用域',
                ]
            },
            'valueerror': {
                'name': 'ValueError',
                'keywords': ['ValueError', 'invalid value'],
                'solutions': [
                    '检查参数值是否有效',
                    '检查数据类型转换',
                ]
            },
            'attributeerror': {
                'name': 'AttributeError',
                'keywords': ['AttributeError', 'has no attribute'],
                'solutions': [
                    '检查对象是否有该属性',
                    '检查属性名是否拼写正确',
                    '检查是否导入了正确的模块',
                ]
            },
            'importerror': {
                'name': 'ImportError',
                'keywords': ['ImportError', 'No module named', 'cannot import'],
                'solutions': [
                    '检查模块是否已安装',
                    '检查导入路径是否正确',
                    '检查循环导入',
                ]
            },
        }

        error_type_lower = error_type.lower()
        for key, pattern in patterns.items():
            if key in error_type_lower or any(k.lower() in error_type_lower for k in pattern['keywords']):
                return pattern

        return {
            'name': 'Unknown',
            'keywords': [],
            'solutions': ['请提供更多错误信息']
        }

    def check_syntax(self, filepath: str) -> str:
        """检查语法错误"""
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.workspace, filepath)

        if not os.path.exists(filepath):
            return f"文件不存在: {filepath}"

        ext = os.path.splitext(filepath)[1].lower()

        try:
            if ext == '.py':
                return self._check_python_syntax(filepath)
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                return self._check_js_ts_syntax(filepath)
            elif ext == '.vue':
                return self._check_vue_syntax(filepath)
            elif ext == '.go':
                return self._check_go_syntax(filepath)
            elif ext == '.java':
                return self._check_java_syntax(filepath)
            elif ext == '.rs':
                return self._check_rust_syntax(filepath)
            else:
                return f"暂不支持检查 {ext} 文件"
        except Exception as e:
            logger.error(f"check_syntax failed: {e}")
            return f"检查失败: {str(e)}"

    def _check_python_syntax(self, filepath: str) -> str:
        """检查 Python 语法"""
        import ast

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()

            ast.parse(source, filename=filepath)
            return f"✅ {filepath} 语法正确"

        except SyntaxError as e:
            return f"❌ 语法错误 (行 {e.lineno}): {e.msg}\n  {e.text}"
        except Exception as e:
            return f"❌ 检查失败: {e}"

    def _check_js_ts_syntax(self, filepath: str) -> str:
        """检查 JavaScript/TypeScript 语法（基础检查）"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        errors = []

        # 括号匹配检查
        for open_char, close_char in [('(', ')'), ('[', ']'), ('{', '}')]:
            open_count = content.count(open_char)
            close_count = content.count(close_char)
            if open_count != close_count:
                errors.append(f"{open_char}/{close_char} 不匹配: 开 {open_count}, 闭 {close_count}")

        # 引号检查
        for quote in ['"', "'", '`']:
            if content.count(quote) % 2 != 0:
                errors.append(f"引号 {quote} 不匹配")

        # 基础正则检查
        common_errors = [
            (r'=\s*{[^}]*$', '可能的赋值错误'),
            (r'function\s+\(', 'function 关键字后有空格'),
        ]

        if errors:
            return f"❌ 潜在错误:\n  " + "\n  ".join(errors)
        return f"✅ {filepath} 初步检查通过"

    def _check_vue_syntax(self, filepath: str) -> str:
        """检查 Vue 文件语法"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查 template/script/style 标签
            required_tags = ['<template', '<script']
            for tag in required_tags:
                if tag not in content:
                    return f"⚠️ 缺少 {tag} 标签"

            # 检查配对
            for tag in ['template', 'script', 'style']:
                open_count = content.count(f'<{tag}')
                close_count = content.count(f'</{tag}>')
                if open_count != close_count:
                    return f"❌ <{tag}> 标签不匹配"

            return self._check_js_ts_syntax(filepath)
        except Exception as e:
            return f"❌ 检查失败: {e}"

    def _check_go_syntax(self, filepath: str) -> str:
        """检查 Go 文件语法（基础）"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            errors = []

            # 括号检查
            for open_c, close_c in [('(', ')'), ('[', ']'), ('{', '}')]:
                if content.count(open_c) != content.count(close_c):
                    errors.append(f"{open_c}/{close_c} 不匹配")

            if errors:
                return f"❌ 潜在错误:\n  " + "\n  ".join(errors)
            return f"✅ {filepath} 初步检查通过"
        except Exception as e:
            return f"❌ 检查失败: {e}"

    def _check_java_syntax(self, filepath: str) -> str:
        """检查 Java 文件语法（基础）"""
        return self._check_js_ts_syntax(filepath)

    def _check_rust_syntax(self, filepath: str) -> str:
        """检查 Rust 文件语法（基础）"""
        return self._check_js_ts_syntax(filepath)

    def find_similar_code(self, keyword: str, limit: int = 10) -> str:
        """查找相似代码"""
        try:
            results = self._file_index.search_by_keyword(keyword)
            if not results:
                return f"未找到包含 '{keyword}' 的代码"

            output = f"找到 {len(results)} 个相关文件:\n"
            for i, filepath in enumerate(results[:limit], 1):
                output += f"{i}. {filepath}\n"

            if len(results) > limit:
                output += f"\n... 还有 {len(results) - limit} 个文件"

            return output
        except Exception as e:
            logger.error(f"find_similar_code failed: {e}")
            return f"搜索失败: {str(e)}"

    def get_file_info(self, filepath: str) -> str:
        """获取文件信息"""
        try:
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.workspace, filepath)

            if not os.path.exists(filepath):
                return f"文件不存在: {filepath}"

            stat = os.stat(filepath)
            ext = os.path.splitext(filepath)[1].lower()

            info = {
                'path': filepath,
                'size': stat.st_size,
                'extension': ext,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            }

            # 尝试统计行数
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                info['lines'] = lines
            except:
                pass

            output = f"文件信息:\n"
            output += f"  路径: {info['path']}\n"
            output += f"  大小: {info['size']} bytes\n"
            output += f"  类型: {info['extension']}\n"
            output += f"  修改: {info['modified']}\n"

            if 'lines' in info:
                output += f"  行数: {info['lines']}\n"

            return output
        except Exception as e:
            logger.error(f"get_file_info failed: {e}")
            return f"获取信息失败: {str(e)}"


from datetime import datetime

# 支持配置的单例
_tools: Optional[Tools] = None
_tools_lock = threading.Lock()


def get_tools(workspace: str = None, config: Any = None) -> Tools:
    """获取 Tools 单例"""
    global _tools

    if _tools is None:
        with _tools_lock:
            if _tools is None:
                # 如果传入 config，优先使用 config 中的 workspace
                if config and hasattr(config, 'workspace'):
                    if config.workspace.path:
                        workspace = config.workspace.path

                _tools = Tools(workspace)
                logger.info("Created new Tools instance")

    return _tools


def reset_tools():
    """重置 Tools 单例"""
    global _tools
    _tools = None
    logger.info("Reset Tools singleton")
