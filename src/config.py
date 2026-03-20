"""
配置管理 - 统一的配置加载和管理
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class LLMConfig:
    """LLM 配置"""
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class StorageConfig:
    """存储配置"""
    path: str = ""
    use_sqlite: bool = False


@dataclass
class WorkspaceConfig:
    """工作区配置"""
    path: str = ""
    exclude_dirs: List[str] = field(default_factory=lambda: [
        '.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode'
    ])
    include_extensions: List[str] = field(default_factory=lambda: [
        '.py', '.js', '.ts', '.vue', '.go', '.java', '.rs', '.php', '.cs', '.rb'
    ])


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    file_path: str = ""


@dataclass
class DebugMCPConfig:
    """Debug MCP 主配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    log: LogConfig = field(default_factory=LogConfig)

    def __post_init__(self):
        """初始化默认值"""
        # LLM 配置
        if not self.llm.api_key:
            self.llm.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not self.llm.base_url:
            self.llm.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        # 工作区配置
        if not self.workspace.path:
            self.workspace.path = os.getcwd()

        # 存储配置
        if not self.storage.path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.storage.path = os.path.join(
                os.path.dirname(current_dir),
                "cases",
                "debug_cases.json"
            )

    @classmethod
    def from_env(cls) -> "DebugMCPConfig":
        """从环境变量加载配置"""
        llm_config = LLMConfig(
            model=os.getenv("DEBUG_MCP_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=int(os.getenv("DEBUG_MCP_TIMEOUT", "30")),
            max_retries=int(os.getenv("DEBUG_MCP_MAX_RETRIES", "3")),
        )

        storage_config = StorageConfig(
            path=os.getenv("DEBUG_MCP_STORAGE_PATH", ""),
            use_sqlite=os.getenv("DEBUG_MCP_USE_SQLITE", "false").lower() == "true",
        )

        workspace_config = WorkspaceConfig(
            path=os.getenv("DEBUG_MCP_WORKSPACE", ""),
        )

        log_config = LogConfig(
            level=os.getenv("DEBUG_MCP_LOG_LEVEL", "INFO"),
            file_path=os.getenv("DEBUG_MCP_LOG_FILE", ""),
        )

        return cls(
            llm=llm_config,
            storage=storage_config,
            workspace=workspace_config,
            log=log_config,
        )


# 全局配置实例
_config: Optional[DebugMCPConfig] = None


def get_config() -> DebugMCPConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = DebugMCPConfig.from_env()
    return _config


def set_config(config: DebugMCPConfig):
    """设置全局配置"""
    global _config
    _config = config


def reset_config():
    """重置配置"""
    global _config
    _config = None
