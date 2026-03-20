# Debug MCP - 智能调试 Agent

一个会"记住错误"的智能调试工具，自动排查问题并积累解决方案。

## 特点

- 🔍 **自动排查** - 智能分析错误，定位根因
- 📚 **错误记忆** - 自动保存排查记录，下次类似问题秒解
- 🛡️ **主动预防** - 代码预检，提前发现风险
- 📊 **趋势分析** - 了解错误模式针对性学习
- ⭐ **质量评分** - 高评价方案优先推荐
- 🧠 **ReAct 推理** - 思考 → 行动 → 观察 → 反思
- 🔌 **MCP 协议** - 支持 Claude Desktop、Cursor
- 🌐 **多 LLM** - DeepSeek / OpenAI / Anthropic
- 📁 **无需数据库** - 纯 JSON 文件存储案例

---

## 新人使用步骤

### 1. 安装

```bash
git clone https://github.com/你的用户名/debug-mcp.git
cd debug-mcp
pip install -e .
```

### 2. 配置 API Key（二选一）

**方式一：创建 .env 文件**
```bash
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY
```

**方式二：直接传入**
```python
agent = DebugAgent(api_key="sk-your-key")
```

### 3. 使用（两种方式）

#### 方式 A：Python 直接调用（推荐）

```python
from src.agent import DebugAgent

agent = DebugAgent()

# 排查问题
result = agent.debug("TypeError: Cannot read property 'id' of undefined")

print(result)
```

#### 方式 B：MCP Server（需要 Claude Desktop）

配置 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "debug-mcp": {
      "command": "python",
      "args": ["-m", "src.server"]
    }
  }
}
```

重启 Claude Desktop，然后直接说：
- "排查一下这个错误"
- "看看这个 bug"

---

## MCP 工具列表

| 工具 | 说明 |
|------|------|
| `debug` | 排查问题 - 输入错误信息，返回解决方案 |
| `search_case` | 搜索历史案例 |
| `list_cases` | 列出所有案例 |
| `get_case` | 查看案例详情 |
| `delete_case` | 删除案例 |
| `mark_effective` | 标记方案有效性（帮助改进匹配） |
| `get_recommended_fixes` | 获取高评价解决方案 |
| `pre_check_code` | 代码风险预检（主动预防） |
| `get_weekly_report` | 获取本周错误报告 |
| `get_error_trends` | 获取错误趋势分析 |
| `get_stats` | 统计信息 |
| `clear_memory` | 清空记忆 |
| `search_code` | 搜索代码文件 |
| `read_file` | 读取文件内容 |
| `grep` | 正则搜索 |
| `check_syntax` | 语法检查 |
| `list_files` | 列出文件 |
| `refresh_index` | 刷新索引 |

---

## 如何避免重复犯错？

使用以下 5 个最佳实践：

### 1️⃣ 描述错误要具体

```python
# ❌ 太笼统
agent.debug("程序出错了")

# ✅ 具体描述
agent.debug("TypeError: Cannot read property 'id' of undefined")
```

### 2️⃣ 看到 `found_in_history: True` 直接用历史方案

```python
result = agent.debug("Cannot read property 'id' of undefined")

# 如果 found_in_history: True
# 直接使用 result['solution']，无需重新排查
```

### 3️⃣ 定期查看高频错误

```python
# 查看最常遇到的错误，针对性预防
agent.list_cases(limit=10)  # 高频错误排行
agent.get_stats()           # 统计信息
agent.get_weekly_report()   # 本周报告
```

### 4️⃣ 使用预检主动预防

```python
# 在编码时主动检查风险
agent.pre_check(code="your_code_here")

# 或使用 MCP
# "检查一下这段代码有没有风险"
```

### 5️⃣ 标记方案有效性帮助改进

```python
# 如果方案有效
agent.memory.mark_effective(case_id, effective=True)

# 如果方案无效
agent.memory.mark_effective(case_id, effective=False)

# 获取高评价方案
agent.memory.get_effective_cases(min_rating=0.5)
```

---

### 核心思想

这个 MCP 的价值在于**积累**：
- 用得越多，案例库越丰富
- 标记有效性 → 匹配算法越精准
- 定期查看错误趋势 → 针对性学习预防

---

## 示例

```python
from src.agent import DebugAgent

agent = DebugAgent(api_key="sk-xxx")

# 第一次排查
result = agent.debug("TypeError: Cannot read property 'id' of undefined")
# 输出：
# {
#   "success": True,
#   "root_cause": "接口返回数据为null时未做空值检查",
#   "fix_solution": "使用 data?.id 或 data || {}",
#   "steps": [{"action": "...", "observation": "..."}],
#   "found_in_history": False
# }

# 第二次排查相同错误（自动匹配历史）
result = agent.debug("Cannot read property 'id' of undefined")
# 输出：
# {
#   "success": True,
#   "found_in_history": True,
#   "fix_solution": "使用 data?.id 或 data || {}",
#   "history_case": {...}
# }
```

---

## 项目结构

```
debug-mcp/
├── src/
│   ├── agent.py        # Debug Agent 核心
│   ├── memory.py       # 案例库（JSON 文件）
│   ├── tools.py        # 工具集
│   └── server.py       # MCP Server
├── cases/              # 案例存储目录（自动创建）
│   └── debug_cases.json
└── .env               # API Key 配置
```

---

## 案例库

- 位置：`cases/debug_cases.json`
- **无需数据库**，纯文件存储
- 每次排查自动保存
- 下次遇到类似问题自动匹配

---

## API

```python
from src.agent import DebugAgent

agent = DebugAgent(api_key="sk-xxx")

# 排查问题
result = agent.debug("错误信息")

# 搜索历史案例
cases = agent.search_history(["关键词"])

# 获取统计
stats = agent.get_stats()

# 主动预防：检查代码风险
result = agent.pre_check(code="your code here")

# 获取高评价方案
effective_cases = agent.memory.get_effective_cases(min_rating=0.5)

# 标记方案是否有效
agent.memory.mark_effective(case_id, effective=True)

# 获取周报
weekly_report = agent.memory.get_weekly_report()

# 获取趋势分析
trends = agent.memory.get_error_trends(days=30)

# 清空记忆
agent.clear_memory()
```

---

## 配置选项

```python
agent = DebugAgent(
    api_key="sk-xxx",           # API Key（必须）
    model="deepseek-chat",      # 模型，默认 deepseek-chat
    max_steps=5,                # 最大排查步骤
    case_file="cases/debug_cases.json"  # 案例库路径
)
```

---

## 支持的模型

| 模型 | 配置 |
|------|------|
| DeepSeek（默认） | `model="deepseek-chat"` |
| OpenAI | `model="gpt-4"` |
| Anthropic | `model="claude-3-opus"` |
| Ollama | `model="llama2"` |

---

## 给 Claude 的系统规则

如果你是用户，可以在对话中告诉 Claude 以下规则（让它帮你解决问题时更聪明）：

```
你是一个调试助手。在解决问题时：
1. 每次尝试新方法前，先问用户确认
2. 如果一个方法失败，不要用相同方法重试
3. 可以调用 debug-mcp 预检工具检查风险
4. 避免重复尝试已经失败的方法
5. 遇到不确定的问题，先搜索历史案例
```

让 Claude 每次尝试前先用 `pre_check_code` 检查一下代码风险。

---

**有问题？直接在项目中提 Issue！**
