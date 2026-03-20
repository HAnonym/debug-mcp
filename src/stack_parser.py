"""
堆栈跟踪解析器 - 智能解析各种语言的错误堆栈
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class StackFrame:
    """堆栈帧"""
    file: str
    line: int
    function: Optional[str]
    raw: str


@dataclass
class ParsedError:
    """解析后的错误"""
    error_type: str
    message: str
    frames: List[StackFrame]
    main_file: Optional[str]
    main_line: Optional[int]


class StackParser:
    """堆栈解析器"""

    # Python 堆栈模式
    PYTHON_PATTERN = re.compile(
        r'File "([^"]+)", line (\d+)(?:, in ([^\n]+))?\n\s*(.+)'
    )

    # JavaScript/Node.js 堆栈模式
    JS_PATTERN = re.compile(
        r'(?:at |@)([^\s]+)(?:\s+\(([^)]+):(\d+):(\d+)\)|:?(\d+):(\d+))'
    )

    # Java 堆栈模式
    JAVA_PATTERN = re.compile(
        r'\tat ([^.]+)\.([^.]+)\(([^.]+):(\d+)\)'
    )

    # 错误类型模式
    ERROR_TYPE_PATTERN = re.compile(
        r'(\w+Error|\w+Exception):\s*(.+)'
    )

    def parse(self, stack_trace: str) -> ParsedError:
        """
        解析堆栈跟踪

        Args:
            stack_trace: 错误堆栈文本

        Returns:
            ParsedError 对象
        """
        lines = stack_trace.strip().split('\n')

        # 提取错误类型和消息
        error_type = "Error"
        message = ""

        for line in lines[:5]:
            match = self.ERROR_TYPE_PATTERN.search(line)
            if match:
                error_type = match.group(1)
                message = match.group(2).strip()
                break

        # 解析堆栈帧
        frames = []

        # 尝试 Python 格式
        frames = self._parse_python(stack_trace)
        if not frames:
            # 尝试 JavaScript 格式
            frames = self._parse_javascript(stack_trace)
        if not frames:
            # 尝试 Java 格式
            frames = self._parse_java(stack_trace)

        # 获取主要文件位置
        main_file = frames[0].file if frames else None
        main_line = frames[0].line if frames else None

        return ParsedError(
            error_type=error_type,
            message=message,
            frames=frames,
            main_file=main_file,
            main_line=main_line
        )

    def _parse_python(self, stack: str) -> List[StackFrame]:
        """解析 Python 堆栈"""
        frames = []

        for match in self.PYTHON_PATTERN.finditer(stack):
            file_path = match.group(1)
            line = int(match.group(2))
            function = match.group(3) if match.group(3) else None

            frames.append(StackFrame(
                file=file_path,
                line=line,
                function=function,
                raw=match.group(0)
            ))

        return frames

    def _parse_javascript(self, stack: str) -> List[StackFrame]:
        """解析 JavaScript 堆栈"""
        frames = []

        for stack_line in stack.split('\n'):
            match = self.JS_PATTERN.search(stack_line)
            if match:
                function = match.group(1)
                if match.group(2):  # 有文件名
                    file_path = match.group(2)
                    line_num = int(match.group(3))
                else:  # 只有行号
                    file_path = "unknown"
                    line_num = int(match.group(5))

                frames.append(StackFrame(
                    file=file_path,
                    line=line_num,
                    function=function,
                    raw=stack_line.strip()
                ))

        return frames

    def _parse_java(self, stack: str) -> List[StackFrame]:
        """解析 Java 堆栈"""
        frames = []

        for match in self.JAVA_PATTERN.finditer(stack):
            class_name = match.group(1)
            method = match.group(2)
            file_name = match.group(3)
            line = int(match.group(4))

            frames.append(StackFrame(
                file=file_name,
                line=line,
                function=f"{class_name}.{method}",
                raw=match.group(0)
            ))

        return frames

    def format_summary(self, parsed: ParsedError) -> str:
        """格式化摘要"""
        output = []

        output.append(f"❌ {parsed.error_type}: {parsed.message}")
        output.append("")

        if parsed.frames:
            output.append("📍 错误位置:")
            main = parsed.frames[0]
            output.append(f"   文件: {main.file}")
            output.append(f"   行号: {main.line}")
            if main.function:
                output.append(f"   函数: {main.function}")
            output.append("")

            if len(parsed.frames) > 1:
                output.append("📚 调用堆栈:")
                for i, frame in enumerate(parsed.frames[:5], 1):
                    func = f" → {frame.function}" if frame.function else ""
                    output.append(f"   {i}. {frame.file}:{frame.line}{func}")

        return "\n".join(output)


def parse_stack_trace(stack_trace: str) -> ParsedError:
    """便捷函数：解析堆栈"""
    parser = StackParser()
    return parser.parse(stack_trace)


def format_stack_summary(stack_trace: str) -> str:
    """便捷函数：格式化堆栈摘要"""
    parser = StackParser()
    parsed = parser.parse(stack_trace)
    return parser.format_summary(parsed)
