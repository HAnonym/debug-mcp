"""
Debug Agent - 智能调试 Agent 核心（优化版）
- 使用 httpx 替代 requests
- 添加重试机制
- 改进关键词提取
- 改进错误处理
"""

import json
import os
import re
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from functools import lru_cache

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_config, DebugMCPConfig
from .memory import Memory, get_memory
from .tools import Tools, get_tools
from .logger import get_logger
from .local_db import get_error_info, get_fix_code, ERROR_DB

logger = get_logger("debug-mcp.agent")




class DebugAgent:
    """智能调试 Agent - 自动排查问题并记住错误（优化版）"""

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        workspace: str = None,
        storage_path: str = None,
        config: DebugMCPConfig = None
    ):
        # 加载配置
        self.config = config or get_config()

        # 优先使用传入的参数，否则使用配置
        self.model = model or self.config.llm.model

        # 自动检测 API Key 来源
        if api_key:
            self.api_key = api_key
        else:
            # 尝试从环境变量获取
            model_lower = (model or self.config.llm.model).lower()
            if "claude" in model_lower:
                self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
            elif "gpt" in model_lower or "openai" in model_lower:
                self.api_key = os.getenv("OPENAI_API_KEY", "")
            elif "ollama" in model_lower:
                self.api_key = ""  # Ollama 不需要 API Key
            else:
                # 默认 DeepSeek
                self.api_key = self.config.llm.api_key or os.getenv("DEEPSEEK_API_KEY", "")

        # 自动检测 Base URL
        if base_url:
            self.base_url = base_url
        else:
            model_lower = (model or self.config.llm.model).lower()
            if "claude" in model_lower:
                self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
            elif "gpt" in model_lower or "openai" in model_lower:
                self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
            elif "ollama" in model_lower:
                self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            else:
                self.base_url = self.config.llm.base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        self.timeout = self.config.llm.timeout
        self.max_retries = self.config.llm.max_retries

        # 本地模式：不使用 AI
        self.use_local_only = os.getenv("DEBUG_MCP_LOCAL_ONLY", "false").lower() == "true"
        if not self.api_key:
            self.use_local_only = True
            logger.info("No API key found, using local mode")

        # 工作区
        self.workspace = workspace or self.config.workspace.path or os.getcwd()

        # 初始化组件
        self.memory = get_memory(storage_path, self.config)
        self.tools = get_tools(self.workspace, self.config)

        logger.info(f"DebugAgent initialized: model={self.model}, workspace={self.workspace}")

    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """调用 LLM API（带重试）"""
        if not self.api_key:
            logger.error("API key not configured")
            return "错误: 未配置 API Key"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            return self._call_llm_with_retry(messages)
        except Exception as e:
            logger.error(f"LLM call failed after retries: {e}")
            return f"调用失败: {str(e)}"

    def _detect_provider(self) -> str:
        """检测 LLM 提供商"""
        model = self.model.lower()
        base_url = self.base_url.lower()

        if "claude" in model or "anthropic" in base_url:
            return "anthropic"
        elif "gpt" in model or "openai" in base_url:
            return "openai"
        elif "ollama" in base_url:
            return "ollama"
        else:
            return "openai兼容"  # DeepSeek 等

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)),
        reraise=True
    )
    def _call_llm_with_retry(self, messages: List[Dict]) -> str:
        """带重试的 LLM 调用"""
        provider = self._detect_provider()
        logger.debug(f"Calling LLM: {self.base_url}, model: {self.model}, provider: {provider}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                # 根据不同提供商构建请求
                if provider == "anthropic":
                    return self._call_anthropic(client, messages)
                elif provider == "ollama":
                    return self._call_ollama(client, messages)
                else:
                    # OpenAI 兼容格式 (DeepSeek, OpenAI 等)
                    return self._call_openai_compatible(client, messages)

        except httpx.TimeoutException:
            logger.warning("Request timed out, will retry")
            raise
        except httpx.ConnectError as e:
            logger.warning(f"Connection error: {e}, will retry")
            raise
        except httpx.NetworkError:
            logger.warning("Network error, will retry")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {e}")
            raise

    def _call_openai_compatible(self, client: httpx.Client, messages: List[Dict]) -> str:
        """调用 OpenAI 兼容 API (DeepSeek, OpenAI 等)"""
        response = client.post(
            f"{self.base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": 0.7
            }
        )

        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            logger.debug(f"LLM response received: {len(result)} chars")
            return result
        elif response.status_code == 401:
            logger.error("Invalid API key")
            return "错误: API Key 无效"
        elif response.status_code == 429:
            logger.warning("Rate limited, will retry")
            raise httpx.RateLimitError("Rate limited", response=response)
        else:
            logger.error(f"API returned status {response.status_code}")
            return f"API 调用失败: {response.status_code}"

    def _call_anthropic(self, client: httpx.Client, messages: List[Dict]) -> str:
        """调用 Anthropic Claude API"""
        # 转换消息格式
        system_prompt = ""
        user_prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                user_prompt = msg["content"]

        # 构建请求
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        # 获取模型名称
        model = self.model
        if "haiku" in model:
            model = "claude-3-haiku-20240307"
        elif "sonnet" in model:
            model = "claude-3-5-sonnet-20241022"
        elif "opus" in model:
            model = "claude-3-opus-20240229"

        data = {
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        if system_prompt:
            data["system"] = system_prompt

        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()["content"][0]["text"]
            logger.debug(f"Claude response received: {len(result)} chars")
            return result
        elif response.status_code == 401:
            logger.error("Invalid API key")
            return "错误: API Key 无效"
        elif response.status_code == 429:
            logger.warning("Rate limited, will retry")
            raise httpx.RateLimitError("Rate limited", response=response)
        else:
            logger.error(f"Claude API returned status {response.status_code}")
            return f"API 调用失败: {response.status_code}"

    def _call_ollama(self, client: httpx.Client, messages: List[Dict]) -> str:
        """调用 Ollama 本地模型"""
        # 转换消息格式
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += f"System: {msg['content']}\n"
            elif msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"

        response = client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            result = response.json()["response"]
            logger.debug(f"Ollama response received: {len(result)} chars")
            return result
        else:
            logger.error(f"Ollama API returned status {response.status_code}")
            return f"API 调用失败: {response.status_code}"

    def _extract_keywords(self, problem: str) -> List[str]:
        """提取关键词（改进版）"""
        keywords = []

        # 1. 提取错误类型
        error_patterns = [
            r'\b(TypeError|SyntaxError|ReferenceError|ValueError|AttributeError|'
            r'ImportError|OSError|RuntimeError|Error|Exception)\b',
        ]
        for pattern in error_patterns:
            match = re.search(pattern, problem, re.IGNORECASE)
            if match:
                keywords.append(match.group(1))

        # 2. 提取文件路径和行号
        file_path_pattern = r'([a-zA-Z]:[\\/])?[^:\s]+:\d+|:(\d+)'
        file_matches = re.findall(file_path_pattern, problem)
        if file_matches:
            for match in file_matches:
                filepath = match[0] or match[1]
                if filepath and len(filepath) > 2:
                    keywords.append(filepath)

        # 3. 提取变量名/函数名（带引号或特殊格式）
        name_patterns = [
            r"'([^']+)'",           # 'variable'
            r'"([^"]+)"',           # "variable"
            r'`([^`]+)`',           # `variable`
            r'\b(\w+)\s+(?:is not|undefined|cannot read)\b',  # xxx is not defined
            r'\b(\w+)\.\w+',        # obj.property
            r'\b(\w+)\(',           # function(
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, problem)
            keywords.extend(matches)

        # 4. 通用关键词（4个字符以上的单词）
        words = re.findall(r'\b\w{4,}\b', problem)
        common_words = {'this', 'that', 'from', 'with', 'have', 'been', 'were', 'what', 'when', 'where', 'which', 'will', 'your', 'more', 'also'}
        significant_words = [w for w in words if w.lower() not in common_words]
        keywords.extend(significant_words[:5])

        # 去重并返回
        return list(set(keywords))[:10]

    def _classify_error(self, problem: str) -> Dict:
        """错误分类（可扩展版）"""
        problem_lower = problem.lower()

        # 分类定义
        classifications = {
            'frontend': {
                'keywords': ['vue', 'react', 'javascript', 'typescript', 'browser',
                           'undefined', 'null', 'component', 'props', 'state', 'dom', 'window', 'document'],
                'tools': ['search_code', 'grep', 'read_file']
            },
            'backend': {
                'keywords': ['python', 'flask', 'django', 'node', 'api', 'server',
                           'database', 'sql', 'error', 'exception', 'docker', 'nginx'],
                'tools': ['search_code', 'grep', 'check_syntax']
            },
            'network': {
                'keywords': ['network', 'timeout', 'connection', 'refused', '500', '404', '503', '502', 'host', 'port', 'dns'],
                'tools': ['check_syntax']
            },
            'mobile': {
                'keywords': ['android', 'ios', 'flutter', 'react native', 'mobile', 'app'],
                'tools': ['search_code', 'grep']
            },
            'devops': {
                'keywords': ['docker', 'kubernetes', 'k8s', 'ci', 'cd', 'pipeline', 'deploy'],
                'tools': ['search_code', 'grep']
            }
        }

        # 匹配分类
        for type_name, config in classifications.items():
            if any(kw in problem_lower for kw in config['keywords']):
                logger.debug(f"Classified as: {type_name}")
                return {
                    'type': type_name,
                    'tools': config['tools']
                }

        logger.debug("Classification: unknown")
        return {'type': 'unknown', 'tools': ['search_code', 'grep']}

    def _get_local_solution(self, problem: str, classification: Dict, error_pattern: Dict) -> Optional[Dict]:
        """
        获取本地解决方案（无需 AI）

        Returns:
            包含 root_cause, solution, prevention, fix_code 的字典
        """
        problem_lower = problem.lower()
        error_type = error_pattern.get('name', '')

        # 1. 使用 local_db 查找解决方案
        error_info = get_error_info(problem)

        if error_info:
            logger.info(f"Found local solution for: {error_info.get('name')}")

            # 获取修复代码
            fix_code = error_info.get('fix_code')
            fix_code_text = ""
            if fix_code:
                if fix_code.get('template'):
                    fix_code_text = f"\n\n📝 修复代码模板:\n```\n{fix_code['template']}\n```"
                elif fix_code.get('before') and fix_code.get('after'):
                    fix_code_text = f"\n\n📝 修复示例:\n```\n# 修复前:\n{fix_code['before']}\n\n# 修复后:\n{fix_code['after']}\n```"

            return {
                'root_cause': error_info.get('root_cause', '未知'),
                'solution': '本地方案:\n' + '\n'.join(f"- {s}" for s in error_info.get('solutions', [])) + fix_code_text,
                'prevention': '本地建议:\n' + '\n'.join(f"- {p}" for p in error_info.get('prevention', [])),
                'category': error_info.get('category', 'Unknown')
            }

        # 2. 尝试模糊匹配本地 DB
        for key, info in ERROR_DB.items():
            if key in problem_lower:
                logger.info(f"Found local solution via keyword: {key}")
                fix_code = info.get('fix_code', {})
                fix_code_text = ""
                if fix_code and fix_code.get('template'):
                    fix_code_text = f"\n\n📝 修复代码模板:\n```\n{fix_code['template']}\n```"

                return {
                    'root_cause': info.get('root_cause', '未知'),
                    'solution': '本地方案:\n' + '\n'.join(f"- {s}" for s in info.get('solutions', [])) + fix_code_text,
                    'prevention': '本地建议:\n' + '\n'.join(f"- {p}" for p in info.get('prevention', [])),
                    'category': info.get('category', 'Unknown')
                }

        # 3. 返回通用建议
        logger.info("No local solution found, using generic advice")
        return {
            'root_cause': "无法确定具体根因，建议查看错误信息和堆栈跟踪",
            'solution': '通用解决方案:\n- 查看完整错误信息和堆栈跟踪\n- 检查代码第 N 行的变量/函数\n- 使用日志或断点调试\n- 搜索错误信息获取更多帮助',
            'prevention': '通用预防:\n- 添加输入验证\n- 使用类型检查\n- 编写单元测试\n- 启用 linting',
            'category': 'Unknown'
        }

    def _generate_fix_code_with_llm(self, problem: str, error_pattern: Dict) -> str:
        """使用 LLM 生成修复代码"""
        error_type = error_pattern.get('name', 'Unknown')

        system_prompt = f"""你是一个代码修复专家。根据以下错误生成修复代码：

错误类型: {error_type}
错误信息: {problem}

请直接给出修复代码，不需要解释。代码要简洁、准确、可运行。
只返回代码，不要其他内容。"""

        try:
            code = self._call_llm(problem, system_prompt)
            # 提取代码块
            if '```' in code:
                code = code.split('```')[1]
                if code.startswith('python') or code.startswith('javascript') or code.startswith('js'):
                    code = code.split('\n', 1)[1]
                if code.endswith('```'):
                    code = code[:-3]
            return code.strip()
        except Exception as e:
            logger.error(f"Failed to generate fix code: {e}")
            return ""

    def debug(self, problem: str, auto_save: bool = True, use_llm: bool = None) -> Dict:
        """主调试方法"""
        logger.info(f"Debug request: {problem[:100]}...")

        result = {
            'success': False,
            'problem': problem,
            'steps': [],
            'root_cause': None,
            'solution': None,
            'prevention': None,
            'found_in_history': False,
            'history_case': None,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # 1. 提取关键词
            keywords = self._extract_keywords(problem)
            result['steps'].append({
                'step': 1,
                'action': 'extract_keywords',
                'keywords': keywords
            })
            logger.debug(f"Extracted keywords: {keywords}")

            # 2. 搜索历史案例
            history_cases = self.memory.search(keywords)
            if history_cases:
                result['found_in_history'] = True
                result['history_case'] = history_cases[0]
                result['steps'].append({
                    'step': 2,
                    'action': 'search_history',
                    'found': len(history_cases),
                    'top_case': {
                        'id': history_cases[0].get('id'),
                        'occurrences': history_cases[0].get('occurrences', 0)
                    }
                })

                self.memory.increment_occurrence(history_cases[0].get('id'))

                # 如果已有解决方案，直接返回
                if history_cases[0].get('solution'):
                    result['success'] = True
                    result['root_cause'] = history_cases[0].get('root_cause')
                    result['solution'] = history_cases[0].get('solution')
                    result['prevention'] = history_cases[0].get('prevention')
                    logger.info(f"Found solution in history: {history_cases[0].get('id')}")
                    return result

            # 3. 错误分类
            classification = self._classify_error(problem)
            result['steps'].append({
                'step': 3,
                'action': 'classify_error',
                'type': classification['type'],
                'tools': classification['tools']
            })
            logger.debug(f"Error type: {classification['type']}")

            # 4. 使用工具排查
            search_keyword = keywords[0] if keywords else problem[:20]
            search_result = self.tools.search_code(search_keyword)
            result['steps'].append({
                'step': 4,
                'action': 'search_code',
                'result': search_result[:500]
            })

            # 5. 搜索错误模式
            error_pattern = self.tools.search_error_pattern(problem)
            result['steps'].append({
                'step': 5,
                'action': 'search_error_pattern',
                'pattern': error_pattern.get('name'),
                'solutions': error_pattern.get('solutions', [])
            })

            # 6. 生成解决方案（优先使用本地模式）
            should_use_llm = use_llm if use_llm is not None else not self.use_local_only

            if should_use_llm and self.api_key:
                # 使用 LLM
                system_prompt = f"""你是一个调试专家。根据以下信息给出解决方案：

问题: {problem}
关键词: {', '.join(keywords)}
错误类型: {classification['type']}
代码搜索结果: {search_result[:300]}
错误模式: {json.dumps(error_pattern, ensure_ascii=False)}

请给出:
1. 可能的根因
2. 具体解决方案
3. 预防建议

请用中文回复，格式如下:
根因: xxx
解决方案: xxx
预防建议: xxx"""

                llm_result = self._call_llm(problem, system_prompt)

                # 解析 LLM 结果
                root_cause = ""
                solution = ""
                prevention = ""

                for line in llm_result.split('\n'):
                    if line.startswith('根因:'):
                        root_cause = line[3:].strip()
                    elif line.startswith('解决方案:'):
                        solution = line[5:].strip()
                    elif line.startswith('预防建议:'):
                        prevention = line[5:].strip()

                result['root_cause'] = root_cause or llm_result[:200]
                result['solution'] = solution or llm_result[:200]
                result['prevention'] = prevention
                result['mode'] = 'llm'
            else:
                # 使用本地模式
                logger.info("Using local mode (no AI)")
                local_result = self._get_local_solution(problem, classification, error_pattern)
                result['root_cause'] = local_result.get('root_cause', '')
                result['solution'] = local_result.get('solution', '')
                result['prevention'] = local_result.get('prevention', '')
                result['mode'] = 'local'

            result['success'] = True

            # 7. 保存到案例库
            if auto_save:
                case = {
                    'problem': problem,
                    'keywords': keywords,
                    'problem_type': classification['type'],
                    'root_cause': result['root_cause'],
                    'solution': result['solution'],
                    'prevention': result['prevention'],
                }
                case_id = self.memory.add_case(case)

                # 从新案例学习，扩展错误库
                try:
                    from .local_db import learn_from_case
                    learn_from_case(case)
                except Exception as e:
                    logger.debug(f"Failed to learn from case: {e}")

                logger.info(f"Saved new case to memory: {case_id}")

            logger.info("Debug completed successfully")

        except Exception as e:
            logger.error(f"Debug failed: {e}", exc_info=True)
            result['error'] = str(e)

        return result

    def search_cases(self, keywords: str, limit: int = 20) -> List[Dict]:
        """搜索案例"""
        keyword_list = keywords.replace(',', ' ').split()
        return self.memory.search(keyword_list, limit=limit)

    def list_cases(self, limit: int = 10) -> List[Dict]:
        """列出案例"""
        return self.memory.list_cases(limit)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.memory.get_stats()

    def clear_memory(self):
        """清空记忆"""
        self.memory.clear()
        logger.info("Memory cleared")

    def refresh_index(self):
        """刷新文件索引"""
        self.tools.refresh_index(force=True)
        logger.info("File index refreshed")

    def pre_check(
        self,
        code: str = None,
        filepath: str = None,
        action: str = None
    ) -> Dict:
        """
        主动预防：检查代码中可能触发历史错误的模式

        Args:
            code: 要检查的代码字符串
            filepath: 要检查的文件路径
            action: 正在尝试的操作描述（如 "用 try-catch 包裹"、"用正则匹配"）

        Returns:
            包含风险提示的字典
        """
        logger.info(f"Running pre-check for potential issues, action: {action}")

        result = {
            'success': True,
            'risks': [],
            'suggestions': [],
            'checked_count': 0,
            'action_check': None
        }

        # 1. 如果传入了尝试的操作，先检查历史是否有类似失败
        if action:
            action_keywords = self._extract_keywords(action)
            action_related = self.memory.search(action_keywords, limit=5)

            # 查找低评价的方案（可能失败过的）
            failed_solutions = []
            for case in action_related:
                rating = case.get('user_rating')
                if rating is not None and rating < 0.5:
                    failed_solutions.append({
                        'problem': case.get('problem', '')[:50],
                        'root_cause': case.get('root_cause', '')[:50],
                        'solution': case.get('solution', '')[:50],
                        'rating': rating
                    })

            if failed_solutions:
                result['action_check'] = {
                    'warning': '⚠️ 历史上有类似方案被标记为无效，建议换一种方法',
                    'failed_solutions': failed_solutions
                }

        # 2. 获取代码内容
        code_to_check = code
        if filepath and not code:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code_to_check = f.read()
            except Exception as e:
                return {
                    'success': False,
                    'error': f'读取文件失败: {e}'
                }

        if not code_to_check:
            # 如果只有 action 没有 code，至少做历史检查
            result['checked_count'] = len(action_related) if action else 0
            if not result['action_check']:
                result['suggestions'].append({
                    'message': '未检测到明显风险，继续保持！'
                })
            return result

        # 3. 搜索相关历史案例
        code_keywords = self._extract_keywords(code_to_check)
        related_cases = self.memory.search(code_keywords, limit=10)

        # 4. 检查风险模式
        risk_patterns = [
            {
                'pattern': r'\.\w+\([^)]*\)\s*\.\w+',
                'description': '链式调用可能返回 null/undefined',
                'risk_type': 'null_undefined'
            },
            {
                'pattern': r'\[(\w+)\]',
                'description': '数组访问可能越界',
                'risk_type': 'index_out_of_bounds'
            },
            {
                'pattern': r'JSON\.parse\([^)]+\)',
                'description': 'JSON.parse 可能抛出异常',
                'risk_type': 'json_parse'
            },
            {
                'pattern': r'fetch\([^)]+\)',
                'description': 'fetch 需要错误处理',
                'risk_type': 'network_error'
            },
            {
                'pattern': r'await\s+.*\s*\.\s*then\(',
                'description': '混用 await 和 then 可能导致问题',
                'risk_type': 'promise_mix'
            },
        ]

        # 检测风险
        for rp in risk_patterns:
            matches = re.findall(rp['pattern'], code_to_check)
            if matches:
                result['risks'].append({
                    'type': rp['risk_type'],
                    'description': rp['description'],
                    'matches': len(matches),
                    'suggestion': self._get_fix_suggestion(rp['risk_type'])
                })

        # 5. 检查历史案例匹配
        for case in related_cases:
            if case.get('user_rating', 0.5) or 0.5 >= 0.5:  # 使用有效评价的案例
                result['suggestions'].append({
                    'related_problem': case.get('problem', '')[:50],
                    'solution': case.get('solution', '')[:100] if case.get('solution') else None,
                    'root_cause': case.get('root_cause', '')[:50] if case.get('root_cause') else None
                })

        result['checked_count'] = len(related_cases)

        if not result['risks'] and not result['action_check']:
            result['suggestions'].append({
                'message': '未检测到明显风险，继续保持！'
            })

        logger.info(f"Pre-check completed: {len(result['risks'])} risks found")
        return result

    def _get_fix_suggestion(self, risk_type: str) -> str:
        """根据风险类型获取修复建议"""
        suggestions = {
            'null_undefined': '使用可选链 (?.) 和空值合并 (??)',
            'index_out_of_bounds': '访问前检查数组长度',
            'json_parse': '使用 try-catch 包裹 JSON.parse',
            'network_error': '添加 .catch() 或 try-catch 处理错误',
            'promise_mix': '统一使用 async/await'
        }
        return suggestions.get(risk_type, '请检查代码逻辑')


def create_agent(**kwargs) -> DebugAgent:
    """创建 DebugAgent 实例"""
    return DebugAgent(**kwargs)


def get_agent(config: DebugMCPConfig = None) -> DebugAgent:
    """获取 DebugAgent 单例（可选）"""
    # 这里可以根据需要实现单例模式
    return DebugAgent(config=config)


def quick_debug(error: str, api_key: str = None) -> Dict:
    """
    快速调试 - 简化调用接口

    Args:
        error: 错误信息
        api_key: 可选的 API Key

    Returns:
        调试结果字典
    """
    agent = DebugAgent(api_key=api_key)
    return agent.debug(error)
