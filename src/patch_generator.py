"""
自动修复补丁生成器 - 生成可应用的代码修复
"""

import os
import difflib
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Patch:
    """补丁"""
    file: str
    old_lines: List[str]
    new_lines: List[str]
    line_start: int
    line_end: int

    def to_unified_diff(self) -> str:
        """转换为 unified diff 格式"""
        diff = difflib.unified_diff(
            self.old_lines,
            self.new_lines,
            fromfile=self.file,
            tofile=self.file,
            lineterm='',
            n=3
        )
        return '\n'.join(diff)


@dataclass
class FixSuggestion:
    """修复建议"""
    file: str
    line: int
    original: str
    fixed: str
    explanation: str
    patch: Optional[Patch] = None


class PatchGenerator:
    """补丁生成器"""

    # 常见修复模式
    FIX_PATTERNS = {
        'undefined_check': {
            'pattern': r'(\w+)\.(\w+)(?!\?)',
            'fix': r'\1?.\2',
            'desc': '添加可选链'
        },
        'null_check': {
            'pattern': r'(\w+)\s*\[(\w+)\]',
            'fix': r'\1.get(\2, default)',
            'desc': '使用安全的字典访问'
        },
        'async_await': {
            'pattern': r'\.then\((.*?)\)',
            'fix': r'await \1',
            'desc': '转换为 async/await'
        },
    }

    def generate_fix(self, error_type: str, file_path: str, line: int,
                     context_lines: int = 5) -> Optional[FixSuggestion]:
        """
        生成修复建议

        Args:
            error_type: 错误类型
            file_path: 文件路径
            line: 行号
            context_lines: 上下文行数

        Returns:
            FixSuggestion 对象
        """
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return None

        # 确保行号在有效范围内
        line_start = max(0, line - context_lines - 1)
        line_end = min(len(lines), line + context_lines)

        original_context = lines[line_start:line_end]
        original_text = ''.join(original_context)

        # 根据错误类型生成修复
        fixed_text, explanation = self._apply_fix(error_type, original_text)

        if fixed_text == original_text:
            return None

        # 重新解析行
        fixed_lines = fixed_text.splitlines(keepends=True)

        return FixSuggestion(
            file=file_path,
            line=line,
            original=original_text,
            fixed=fixed_text,
            explanation=explanation,
            patch=Patch(
                file=file_path,
                old_lines=original_context,
                new_lines=fixed_lines,
                line_start=line_start + 1,
                line_end=line_end
            )
        )

    def _apply_fix(self, error_type: str, code: str) -> tuple:
        """应用修复"""
        error_lower = error_type.lower()

        # TypeError 处理
        if 'typeerror' in error_lower or 'cannot read' in error_lower:
            # 检查是否是属性访问问题
            if '.property' in code.lower() or '.id' in code.lower() or '.name' in code.lower():
                fixed = self._fix_optional_chaining(code)
                if fixed != code:
                    return fixed, "添加可选链 (?.) 防止访问 null/undefined 的属性"

        # KeyError 处理
        if 'keyerror' in error_lower:
            fixed = self._fix_dict_access(code)
            if fixed != code:
                return fixed, "使用 .get() 方法安全访问字典"

        # IndexError 处理
        if 'indexerror' in error_lower:
            fixed = self._fix_list_access(code)
            if fixed != code:
                return fixed, "添加索引边界检查"

        # ImportError 处理
        if 'importerror' in error_lower or 'modulenotfound' in error_lower:
            return code, "检查模块是否安装 (pip install / npm install)"

        # SyntaxError 处理
        if 'syntaxerror' in error_lower:
            return code, "检查语法错误：括号、引号是否匹配"

        return code, "请手动修复"

    def _fix_optional_chaining(self, code: str) -> str:
        """修复可选链"""
        # 简单的属性访问转换
        import re
        # 将 obj.prop 转换为 obj?.prop
        fixed = re.sub(r'(\w+)\.(\w+)(?!\?)', r'\1?.\2', code)
        return fixed

    def _fix_dict_access(self, code: str) -> str:
        """修复字典访问"""
        import re
        # 将 dict['key'] 转换为 dict.get('key')
        fixed = re.sub(r"(\w+)\['(\w+)'\]", r"\1.get('\2')", code)
        return fixed

    def _fix_list_access(self, code: str) -> str:
        """修复列表访问"""
        import re
        # 添加边界检查提示
        if re.search(r'\[\d+\]', code):
            # 在访问前添加检查
            return f"# 添加边界检查\n{code}"
        return code

    def generate_patch_file(self, fixes: List[FixSuggestion],
                           output_path: str = "fix.patch") -> str:
        """
        生成补丁文件

        Args:
            fixes: 修复建议列表
            output_path: 输出路径

        Returns:
            补丁内容
        """
        patches = []

        for fix in fixes:
            if fix.patch:
                patches.append(fix.patch.to_unified_diff())

        content = '\n'.join(patches)

        # 保存到文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return content

    def apply_fix(self, fix: FixSuggestion, backup: bool = True) -> bool:
        """
        应用修复

        Args:
            fix: 修复建议
            backup: 是否备份原文件

        Returns:
            是否成功
        """
        if not fix.patch:
            return False

        try:
            file_path = fix.file

            # 备份
            if backup and os.path.exists(file_path):
                backup_path = file_path + '.bak'
                with open(file_path, 'r', encoding='utf-8') as f:
                    with open(backup_path, 'w', encoding='utf-8') as b:
                        b.write(f.read())

            # 读取原文件
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 应用修复
            line_start = fix.patch.line_start - 1
            line_end = fix.patch.line_end

            new_lines = lines[:line_start] + fix.patch.new_lines + lines[line_end:]

            # 写回
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return True

        except Exception as e:
            print(f"应用修复失败: {e}")
            return False

    def format_suggestion(self, fix: FixSuggestion) -> str:
        """格式化修复建议"""
        output = []

        output.append(f"📝 文件: {fix.file}:{fix.line}")
        output.append(f"💡 修复: {fix.explanation}")
        output.append("")
        output.append("修复前:")
        output.append("```")
        output.append(fix.original.strip())
        output.append("```")
        output.append("")
        output.append("修复后:")
        output.append("```")
        output.append(fix.fixed.strip())
        output.append("```")

        if fix.patch:
            output.append("")
            output.append("Diff:")
            output.append("```")
            output.append(fix.patch.to_unified_diff())
            output.append("```")

        return '\n'.join(output)


def generate_fix(error_type: str, file_path: str, line: int) -> Optional[FixSuggestion]:
    """便捷函数：生成修复"""
    generator = PatchGenerator()
    return generator.generate_fix(error_type, file_path, line)
