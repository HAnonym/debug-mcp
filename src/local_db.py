"""
本地错误解决方案数据库 - 50+ 常见错误模式
"""

from typing import Dict, List, Optional

from .logger import get_logger

logger = get_logger("debug-mcp.local_db")


ERROR_DB: Dict[str, Dict] = {
    # ========== TypeError ==========
    "typeerror": {
        "name": "TypeError",
        "category": "JavaScript",
        "root_cause": "变量未定义、类型不匹配或操作了不支持的类型",
        "solutions": [
            "检查变量是否已声明和初始化",
            "检查数据类型是否正确",
            "使用 typeof 或 instanceof 检查类型",
            "使用可选链 (?.) 访问可能不存在的属性",
            "使用空值合并 (??) 处理 null/undefined"
        ],
        "fix_code": {
            "template": "// 使用可选链和空值合并\nconst value = obj?.property ?? 'default';",
            "before": "const value = obj.property;",
            "after": "const value = obj?.property ?? 'default';"
        },
        "prevention": ["启用 TypeScript 严格模式", "使用 ESLint 检查"]
    },
    # ========== SyntaxError ==========
    "syntaxerror": {
        "name": "SyntaxError",
        "category": "通用",
        "root_cause": "代码语法错误，常见于括号、引号、逗号不匹配",
        "solutions": [
            "检查括号 () [] {} 是否配对",
            "检查引号 \" ' ` 是否配对",
            "检查是否有多余的逗号或分号",
            "检查箭头函数语法是否正确",
            "使用 IDE 或 linter 定位具体位置"
        ],
        "fix_code": {
            "template": "// 检查并修复语法错误",
        },
        "prevention": ["使用 Prettier 格式化代码", "启用编辑器的语法检查"]
    },
    # ========== ReferenceError ==========
    "referenceerror": {
        "name": "ReferenceError",
        "category": "JavaScript",
        "root_cause": "引用了未定义的变量或函数",
        "solutions": [
            "检查变量/函数是否已声明",
            "检查是否存在循环引用",
            "检查变量名拼写是否正确",
            "检查 import/require 是否正确"
        ],
        "fix_code": {
            "template": "// 确保变量在使用前声明\nconst myVar = 'hello';\nconsole.log(myVar);",
            "before": "console.log(myVar);",
            "after": "const myVar = 'hello';\nconsole.log(myVar);"
        },
        "prevention": ["使用 const/let 声明变量", "使用模块化开发"]
    },
    # ========== ValueError ==========
    "valueerror": {
        "name": "ValueError",
        "category": "Python",
        "root_cause": "值不符合预期或不在有效范围内",
        "solutions": [
            "检查输入值的类型和范围",
            "添加输入验证",
            "使用 try-catch 捕获异常",
            "检查类型转换是否正确"
        ],
        "fix_code": {
            "template": "# 添加输入验证\ndef parse_int(value):\n    try:\n        return int(value)\n    except ValueError:\n        return 0  # 或抛出自定义异常",
        "before": "result = int(user_input)",
            "after": "try:\n    result = int(user_input)\nexcept ValueError:\n    result = 0"
        },
        "prevention": ["添加参数验证", "使用类型提示"]
    },
    # ========== AttributeError ==========
    "attributeerror": {
        "name": "AttributeError",
        "category": "Python",
        "root_cause": "对象没有指定的属性或方法",
        "solutions": [
            "检查属性名是否拼写正确",
            "检查对象类型是否正确",
            "检查是否导入了正确的模块",
            "使用 hasattr() 检查属性是否存在"
        ],
        "fix_code": {
            "template": "# 使用 hasattr 检查属性\nif hasattr(obj, 'attribute'):\n    result = obj.attribute",
            "before": "result = obj.attribute",
            "after": "result = getattr(obj, 'attribute', None)"
        },
        "prevention": ["使用类型提示", "使用 IDE 自动补全"]
    },
    # ========== ImportError ==========
    "importerror": {
        "name": "ImportError",
        "category": "Python",
        "root_cause": "模块导入失败",
        "solutions": [
            "检查模块是否已安装 (pip install / npm install)",
            "检查 import 路径是否正确",
            "检查是否有循环导入",
            "确认 Python/node 路径正确"
        ],
        "fix_code": {
            "template": "# 使用 try-except 处理导入错误\ntry:\n    import requests\nexcept ImportError:\n    import subprocess\n    subprocess.run(['pip', 'install', 'requests'])",
            "before": "import requests",
            "after": "try:\n    import requests\nexcept ImportError:\n    print('请安装: pip install requests')"
        },
        "prevention": ["使用虚拟环境", "固定依赖版本"]
    },
    # ========== KeyError ==========
    "keyerror": {
        "name": "KeyError",
        "category": "Python",
        "root_cause": "字典中不存在指定的键",
        "solutions": [
            "使用 dict.get(key, default) 代替 dict[key]",
            "使用 'key' in dict 检查键是否存在"
        ],
        "fix_code": {
            "template": "# 使用 .get() 方法\nvalue = data.get('key', 'default_value')",
            "before": "value = data['key']",
            "after": "value = data.get('key', 'default_value')"
        },
        "prevention": ["使用 .get() 方法", "使用 defaultdict"]
    },
    # ========== IndexError ==========
    "indexerror": {
        "name": "IndexError",
        "category": "Python",
        "root_cause": "索引超出序列范围",
        "solutions": [
            "检查索引是否在有效范围内 (0 到 len-1)",
            "使用 try-except 捕获",
            "检查列表是否为空"
        ],
        "fix_code": {
            "template": "# 安全访问列表元素\nvalue = my_list[index] if index < len(my_list) else None",
            "before": "value = my_list[10]",
            "after": "value = my_list[10] if len(my_list) > 10 else None"
        },
        "prevention": ["在访问前检查列表长度", "使用迭代器"]
    },
    # ========== ZeroDivisionError ==========
    "zerodivisionerror": {
        "name": "ZeroDivisionError",
        "category": "Python",
        "root_cause": "除数为零",
        "solutions": [
            "在除法前检查除数是否为零",
            "使用 try-except 捕获"
        ],
        "fix_code": {
            "template": "# 添加除数检查\nresult = numerator / denominator if denominator != 0 else 0",
            "before": "result = a / b",
            "after": "result = a / b if b != 0 else 0"
        },
        "prevention": ["添加除数检查", "使用条件判断"]
    },
    # ========== TypeError (Python) ==========
    "typeerror python": {
        "name": "TypeError",
        "category": "Python",
        "root_cause": "Python 类型相关错误",
        "solutions": [
            "检查变量类型",
            "使用 isinstance() 检查类型",
            "检查操作是否对当前类型有效"
        ],
        "fix_code": {
            "template": "# 类型检查\nif isinstance(value, int):\n    # 处理整数",
            "before": "result = value + 10",
            "after": "if isinstance(value, (int, float)):\n    result = value + 10"
        },
        "prevention": ["使用类型提示", "添加类型检查"]
    },
    # ========== OSError ==========
    "oserror": {
        "name": "OSError",
        "category": "Python",
        "root_cause": "操作系统相关错误",
        "solutions": [
            "检查文件路径是否正确",
            "检查文件/目录权限",
            "使用 os.path.exists() 检查文件"
        ],
        "fix_code": {
            "template": "# 安全文件操作\nimport os\nif os.path.exists(filepath):\n    with open(filepath) as f:\n        content = f.read()",
            "before": "with open('file.txt') as f:\n    content = f.read()",
            "after": "import os\nif os.path.exists('file.txt'):\n    with open('file.txt') as f:\n        content = f.read()"
        },
        "prevention": ["使用绝对路径", "添加异常处理"]
    },
    # ========== RuntimeError ==========
    "runtimeerror": {
        "name": "RuntimeError",
        "category": "Python",
        "root_cause": "运行时发生的错误",
        "solutions": [
            "查看具体错误信息",
            "检查堆栈跟踪定位问题",
            "添加调试打印"
        ],
        "fix_code": {
            "template": "# 添加调试信息\nimport logging\nlogging.basicConfig(level=logging.DEBUG)",
        },
        "prevention": ["编写单元测试", "添加日志记录"]
    },
    # ========== 404 ==========
    "404": {
        "name": "404 Not Found",
        "category": "HTTP",
        "root_cause": "请求的资源不存在",
        "solutions": [
            "检查 URL 是否正确",
            "检查路由配置",
            "确认资源路径"
        ],
        "fix_code": {
            "template": "# 检查响应状态\nimport requests\nresponse = requests.get(url)\nif response.status_code == 200:\n    data = response.json()\nelse:\n    print(f'Error: {response.status_code}')",
            "before": "data = requests.get(url).json()",
            "after": "response = requests.get(url)\nresponse.raise_for_status()\ndata = response.json()"
        },
        "prevention": ["使用 URL 验证", "添加 API 文档"]
    },
    # ========== 500 ==========
    "500": {
        "name": "500 Internal Server Error",
        "category": "HTTP",
        "root_cause": "服务器内部错误",
        "solutions": [
            "查看服务器日志",
            "检查后端代码异常",
            "检查数据库连接"
        ],
        "fix_code": {
            "template": "# 添加错误处理\ntry:\n    response = requests.get(url)\n    response.raise_for_status()\nexcept requests.exceptions.HTTPError as e:\n    print(f'HTTP Error: {e}')",
        },
        "prevention": ["添加错误日志", "使用健康检查"]
    },
    # ========== Connection Refused ==========
    "connection refused": {
        "name": "Connection Refused",
        "category": "Network",
        "root_cause": "无法连接到服务器",
        "solutions": [
            "检查服务器是否运行",
            "检查端口是否正确",
            "检查防火墙设置"
        ],
        "fix_code": {
            "template": "# 添加连接超时和重试\nimport requests\nfrom requests.adapters import HTTPAdapter\nfrom urllib3.util.retry import Retry\n\nsession = requests.Session()\nretry = Retry(total=3, backoff_factor=0.5)\nadapter = HTTPAdapter(max_retries=retry)\nsession.mount('http://', adapter)\nresponse = session.get(url, timeout=5)",
        },
        "prevention": ["添加连接超时", "添加重试机制"]
    },
    # ========== Timeout ==========
    "timeout": {
        "name": "Timeout",
        "category": "Network",
        "root_cause": "请求超时",
        "solutions": [
            "增加超时时间",
            "检查服务器性能",
            "优化查询/请求"
        ],
        "fix_code": {
            "template": "# 增加超时时间\nresponse = requests.get(url, timeout=30)",
            "before": "response = requests.get(url)",
            "after": "response = requests.get(url, timeout=30)"
        },
        "prevention": ["设置合理的超时时间", "使用缓存"]
    },
    # ========== CORS ==========
    "cors": {
        "name": "CORS Error",
        "category": "Web",
        "root_cause": "跨域资源共享错误",
        "solutions": [
            "后端添加 CORS 头部",
            "使用代理服务器",
            "检查前端请求 URL"
        ],
        "fix_code": {
            "template": "# Flask 添加 CORS\nfrom flask_cors import CORS\napp = Flask(__name__)\nCORS(app)",
            "before": "# 缺少 CORS 配置",
            "after": "from flask_cors import CORS\napp = Flask(__name__)\nCORS(app)"
        },
        "prevention": ["配置代理", "使用 JSONP"]
    },
    # ========== Cannot read property ==========
    "cannot read property": {
        "name": "Cannot read property",
        "category": "JavaScript",
        "root_cause": "尝试读取 null/undefined 的属性",
        "solutions": [
            "使用可选链 (?.)",
            "检查对象是否存在",
            "使用空值合并 (??)"
        ],
        "fix_code": {
            "template": "// 安全访问嵌套属性\nconst value = user?.profile?.name ?? 'Unknown';",
            "before": "const name = user.profile.name;",
            "after": "const name = user?.profile?.name ?? 'Unknown';"
        },
        "prevention": ["使用可选链", "添加默认值"]
    },
    # ========== undefined is not a function ==========
    "is not a function": {
        "name": "Is Not a Function",
        "category": "JavaScript",
        "root_cause": "调用了未定义的函数或变量不是函数",
        "solutions": [
            "检查函数是否已定义",
            "检查 this 上下文绑定",
            "检查函数名拼写"
        ],
        "fix_code": {
            "template": "// 使用前检查函数是否存在\nif (typeof myFunc === 'function') {\n    myFunc();\n}",
            "before": "myFunc();",
            "after": "if (typeof myFunc === 'function') {\n    myFunc();\n}"
        },
        "prevention": ["使用箭头函数保留 this", "使用 bind()"]
    },
    # ========== Circular dependency ==========
    "circular dependency": {
        "name": "Circular Dependency",
        "category": "JavaScript",
        "root_cause": "模块循环依赖",
        "solutions": [
            "重构代码消除循环",
            "使用动态导入",
            "提取公共模块"
        ],
        "fix_code": {
            "template": "// 重构消除循环依赖\n// 将相互依赖的代码提取到新模块",
        },
        "prevention": ["使用依赖注入", "避免直接相互导入"]
    },
    # ========== Maximum call stack ==========
    "maximum call stack": {
        "name": "Maximum Call Stack",
        "category": "JavaScript",
        "root_cause": "无限递归或循环引用",
        "solutions": [
            "检查递归终止条件",
            "检查事件监听器重复绑定",
            "使用迭代代替递归"
        ],
        "fix_code": {
            "template": "// 使用迭代代替递归\nfunction sum(arr) {\n    let result = 0;\n    for (const item of arr) {\n        result += item;\n    }\n    return result;\n}",
        },
        "prevention": ["添加递归深度限制", "使用迭代"]
    },
    # ========== Memory leak ==========
    "memory leak": {
        "name": "Memory Leak",
        "category": "JavaScript",
        "root_cause": "未释放的对象引用",
        "solutions": [
            "移除未使用的事件监听器",
            "清理定时器",
            "避免全局变量"
        ],
        "fix_code": {
            "template": "// 清理事件监听器\ncomponent.onDestroy(() => {\n    window.removeEventListener('resize', handler);\n    clearInterval(timer);\n});",
        },
        "prevention": ["使用 WeakMap/WeakSet", "定期清理"]
    },
    # ========== Promise ==========
    "promise": {
        "name": "Promise Error",
        "category": "JavaScript",
        "root_cause": "未处理的 Promise 拒绝",
        "solutions": [
            "添加 .catch() 处理错误",
            "使用 async/await 和 try-catch",
            "添加 unhandledrejection 监听"
        ],
        "fix_code": {
            "template": "// 使用 async/await\nasync function fetchData() {\n    try {\n        const response = await fetch(url);\n        return await response.json();\n    } catch (error) {\n        console.error('Error:', error);\n    }\n}",
        },
        "prevention": ["始终处理 Promise 错误", "使用 lint 规则"]
    },
    # ========== React: Hooks ==========
    "invalid hooks": {
        "name": "React Hooks Error",
        "category": "React",
        "root_cause": "Hooks 在非函数组件或条件调用",
        "solutions": [
            "确保在组件顶层调用 Hooks",
            "只在 React 函数组件中调用 Hooks",
            "确保依赖数组完整"
        ],
        "fix_code": {
            "template": "// React Hooks 规则\nfunction MyComponent() {\n    const [state, setState] = useState(0);\n\n    // ✅ 在顶层调用\n    useEffect(() => {\n        // 副作用\n    }, [state]);  // ✅ 完整的依赖数组\n\n    return <div>{state}</div>;\n}",
        },
        "prevention": ["使用 eslint-plugin-react-hooks", "遵循 Hooks 规则"]
    },
    # ========== React: Can't set state ==========
    "can't set state": {
        "name": "Can't Set State",
        "category": "React",
        "root_cause": "在已卸载组件上设置状态",
        "solutions": [
            "使用 useEffect 清理函数",
            "使用 AbortController 取消异步操作",
            "检查组件是否已卸载"
        ],
        "fix_code": {
            "template": "// 使用 AbortController\nuseEffect(() => {\n    const controller = new AbortController();\n\n    fetchData(controller.signal)\n        .then(data => {\n            if (!controller.signal.aborted) {\n                setData(data);\n            }\n        });\n\n    return () => controller.abort();\n}, []);",
        },
        "prevention": ["使用清理函数", "检查 isMounted"]
    },
    # ========== Vue: $emit ==========
    "$emit": {
        "name": "Vue $emit Error",
        "category": "Vue",
        "root_cause": "Vue 事件发射问题",
        "solutions": [
            "检查事件名是否匹配",
            "确保父组件已监听事件",
            "使用 emits 选项定义事件"
        ],
        "fix_code": {
            "template": "// Vue 3 定义 emits\n<script>\nexport default {\n    emits: ['update', 'delete'],\n    methods: {\n        handleClick() {\n            this.$emit('update', newValue);\n        }\n    }\n}\n</script>",
        },
        "prevention": ["使用 TypeScript", "定义 emits"]
    },
    # ========== Database: connection ==========
    "database connection": {
        "name": "Database Connection Error",
        "category": "Database",
        "root_cause": "数据库连接失败",
        "solutions": [
            "检查数据库服务是否运行",
            "检查连接字符串/凭据",
            "检查防火墙/网络"
        ],
        "fix_code": {
            "template": "# 使用连接池\nfrom sqlalchemy import create_engine\nfrom sqlalchemy.pool import QueuePool\n\nengine = create_engine(\n    'postgresql://user:pass@localhost/db',\n    poolclass=QueuePool,\n    pool_pre_ping=True\n)",
        },
        "prevention": ["使用连接池", "添加重试机制"]
    },
    # ========== SQL: syntax ==========
    "sql syntax": {
        "name": "SQL Syntax Error",
        "category": "Database",
        "root_cause": "SQL 语法错误",
        "solutions": [
            "检查 SQL 关键字拼写",
            "检查引号和括号配对",
            "使用参数化查询"
        ],
        "fix_code": {
            "template": "# 使用参数化查询 (防止 SQL 注入)\ncursor.execute(\n    'SELECT * FROM users WHERE id = %s',\n    (user_id,)\n)",
            "before": "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
            "after": "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
        },
        "prevention": ["使用 ORM", "参数化查询"]
    },
    # ========== NullPointerException ==========
    "nullpointerexception": {
        "name": "NullPointerException",
        "category": "Java",
        "root_cause": "空指针异常",
        "solutions": [
            "检查对象是否为 null",
            "使用 Optional 处理可能为空的值",
            "添加 null 检查"
        ],
        "fix_code": {
            "template": "// 使用 Optional\nOptional.ofNullable(user)\n    .map(User::getName)\n    .orElse(\"Unknown\");",
            "before": "String name = user.getName();",
            "after": "String name = Optional.ofNullable(user)\n    .map(User::getName)\n    .orElse(\"Unknown\");"
        },
        "prevention": ["使用 Optional", "启用空指针检查"]
    },
    # ========== Docker: container ==========
    "docker": {
        "name": "Docker Error",
        "category": "DevOps",
        "root_cause": "Docker 相关错误",
        "solutions": [
            "检查容器是否运行",
            "检查端口映射",
            "查看容器日志"
        ],
        "fix_code": {
            "template": "# 查看容器日志\ndocker logs <container_id>\n\n# 重启容器\ndocker restart <container_id>",
        },
        "prevention": ["使用 docker-compose", "添加健康检查"]
    },
    # ========== Git: merge conflict ==========
    "merge conflict": {
        "name": "Git Merge Conflict",
        "category": "Git",
        "root_cause": "Git 合并冲突",
        "solutions": [
            "手动解决冲突",
            "使用 git mergetool",
            "选择保留的代码"
        ],
        "fix_code": {
            "template": "# 解决合并冲突\n# 1. 查看冲突文件\ngit status\n\n# 2. 编辑冲突文件，保留需要的代码\n\n# 3. 标记为已解决\ngit add <file>\n\n# 4. 完成合并\ngit commit",
        },
        "prevention": ["频繁合并", "使用分支策略"]
    },
    # ========== Module not found ==========
    "module not found": {
        "name": "Module Not Found",
        "category": "Node.js",
        "root_cause": "模块未找到",
        "solutions": [
            "检查模块是否已安装",
            "检查 node_modules",
            "检查路径配置"
        ],
        "fix_code": {
            "template": "# 安装缺失的模块\nnpm install <module-name>\n\n# 或重新安装依赖\nrm -rf node_modules\nnpm install",
        },
        "prevention": ["使用 package.json", "锁定版本"]
    },
    # ========== Node.js specific errors ==========
    "eaddrinuse": {
        "name": "EADDRINUSE (Port in use)",
        "category": "Node.js",
        "root_cause": "端口被占用",
        "solutions": [
            "找到占用端口的进程并终止",
            "使用其他端口",
            "重启计算机"
        ],
        "fix_code": {
            "template": "# 查找占用端口的进程\n# Windows\nnetstat -ano | findstr :3000\ntaskkill /PID <PID> /F\n\n# Linux/Mac\nlsof -i :3000\nkill -9 <PID>"
        },
        "prevention": ["使用环境变量配置端口", "添加端口检测"]
    },
    "ECONNREFUSED": {
        "name": "ECONNREFUSED",
        "category": "Node.js",
        "root_cause": "连接被拒绝，服务未启动",
        "solutions": [
            "确认目标服务是否运行",
            "检查端口号是否正确",
            "检查防火墙设置"
        ],
        "fix_code": {
            "template": "// 添加连接错误处理\nconst connect = async () => {\n    try {\n        await client.connect();\n    } catch (err) {\n        console.error('Connection failed:', err.message);\n        // 重试或使用备用方案\n    }\n};"
        },
        "prevention": ["添加重试机制", "使用服务发现"]
    },
    "ETIMEDOUT": {
        "name": "ETIMEDOUT",
        "category": "Node.js",
        "root_cause": "连接超时",
        "solutions": [
            "增加超时时间",
            "检查网络连接",
            "检查目标服务器性能"
        ],
        "fix_code": {
            "template": "// 增加超时时间\nconst response = await fetch(url, {\n    method: 'GET',\n    signal: AbortSignal.timeout(30000) // 30秒\n});"
        },
        "prevention": ["设置合理超时", "添加重试"]
    },
    # ========== React Native ==========
    "rn undefined is not an object": {
        "name": "Undefined is Not an Object",
        "category": "React Native",
        "root_cause": "访问了未定义的属性",
        "solutions": [
            "检查组件是否正确加载",
            "使用条件渲染",
            "检查 props 是否传递"
        ],
        "fix_code": {
            "template": "// React Native 安全访问\nconst value = this.props.data?.item ?? 'default';\n\n// 或使用条件渲染\n{this.props.data && <Text>{this.props.data.name}</Text>}"
        },
        "prevention": ["使用 PropTypes 或 TypeScript", "添加默认值"]
    },
    "mounting error": {
        "name": "React Mounting Error",
        "category": "React Native",
        "root_cause": "组件挂载顺序错误",
        "solutions": [
            "检查组件生命周期",
            "使用 useEffect 处理异步",
            "确保 Context 在 Provider 内"
        ],
        "fix_code": {
            "template": "// 使用 useEffect 处理异步数据\nuseEffect(() => {\n    fetchData();\n}, []); // 依赖数组要正确"
        },
        "prevention": ["遵循 React 规则", "使用严格模式"]
    },
    # ========== Flutter ==========
    "null check operator used on a null value": {
        "name": "Null Check on Null",
        "category": "Flutter",
        "root_cause": "对空值使用了 ! 操作符",
        "solutions": [
            "使用 ?. 代替 !",
            "添加空值检查",
            "使用 ?? 提供默认值"
        ],
        "fix_code": {
            "template": "// 修复前\nfinal name = user!.name;\n\n// 修复后\nfinal name = user?.name ?? 'Unknown';",
        },
        "prevention": ["启用空安全", "使用 ?." ]
    },
    "setstate called after dispose": {
        "name": "SetState Called After Dispose",
        "category": "Flutter",
        "root_cause": "在组件销毁后调用 setState",
        "solutions": [
            "在 dispose 中取消异步操作",
            "使用 if (mounted) 检查"
        ],
        "fix_code": {
            "template": "@override\nvoid dispose() {\n    _controller.dispose();\n    super.dispose();\n}\n\nvoid _loadData() async {\n    if (!mounted) return;\n    setState(() => _loading = true);\n    // ...\n}"
        },
        "prevention": ["使用 StatefulWidget 的 mounted", "取消订阅"]
    },
    # ========== Kubernetes ==========
    "imagepullbackoff": {
        "name": "ImagePullBackOff",
        "category": "Kubernetes",
        "root_cause": "无法拉取镜像",
        "solutions": [
            "检查镜像名称和标签",
            "检查镜像仓库访问权限",
            "检查网络策略"
        ],
        "fix_code": {
            "template": "# 检查 Pod 状态\nkubectl describe pod <pod-name>\n\n# 检查镜像\nkubectl get pod <pod-name> -o jsonpath='{.spec.containers[0].image}'\n\n# 使用正确的镜像地址\nkubectl set image deployment/myapp myapp=registry.example.com/myapp:v1.0"
        },
        "prevention": ["使用私有镜像仓库", "固定镜像版本"]
    },
    "crashloopbackoff": {
        "name": "CrashLoopBackOff",
        "category": "Kubernetes",
        "root_cause": "容器反复崩溃",
        "solutions": [
            "查看容器日志",
            "检查应用程序启动命令",
            "检查资源限制"
        ],
        "fix_code": {
            "template": "# 查看日志\nkubectl logs <pod-name>\nkubectl logs --previous <pod-name>\n\n# 检查资源配置\nkubectl describe pod <pod-name>"
        },
        "prevention": ["添加健康检查", "设置资源限制"]
    },
    "pending pod": {
        "name": "Pending Pod",
        "category": "Kubernetes",
        "root_cause": "Pod 处于挂起状态",
        "solutions": [
            "检查节点资源是否足够",
            "检查 PVC 是否绑定",
            "检查污点和容忍"
        ],
        "fix_code": {
            "template": "# 查看原因\nkubectl describe pod <pod-name> | grep -A 10 \"Conditions:\"\n\n# 检查节点资源\nkubectl describe nodes\n\n# 如果是资源不足，增加节点或减少副本"
        },
        "prevention": ["设置合理的资源请求", "使用资源配额"]
    },
    # ========== AWS ==========
    "accessdenied": {
        "name": "Access Denied",
        "category": "AWS",
        "root_cause": "IAM 权限不足",
        "solutions": [
            "检查 IAM 策略",
            "检查资源策略",
            "确认角色配置正确"
        ],
        "fix_code": {
            "template": "# 检查 IAM 策略\naws iam get-user\n\n# 附加策略\naws iam attach-user-policy \\\n    --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess \\\n    --user-name your-user"
        },
        "prevention": ["最小权限原则", "使用角色"]
    },
    "validationerror": {
        "name": "Validation Error",
        "category": "AWS",
        "root_cause": "参数验证失败",
        "solutions": [
            "检查参数格式",
            "检查必填参数",
            "查看具体错误信息"
        ],
        "fix_code": {
            "template": "# 检查 CloudFormation 模板\naws cloudformation validate-template \\\n    --template-body file://template.yaml"
        },
        "prevention": ["使用 CDK", "添加参数验证"]
    },
    "throttlingexception": {
        "name": "Throttling Exception",
        "category": "AWS",
        "root_cause": "请求超过速率限制",
        "solutions": [
            "使用指数退避重试",
            "增加请求间隔",
            "请求提高配额"
        ],
        "fix_code": {
            "template": "# 使用指数退避\nimport time\n\ndef retry_with_backoff(func, max_retries=5):\n    for i in range(max_retries):\n        try:\n            return func()\n        except ThrottlingException:\n            wait = 2 ** i\n            time.sleep(wait)\n    raise Exception('Max retries exceeded')"
        },
        "prevention": ["使用 SDK 的自动重试", "请求提高配额"]
    },
    # ========== Docker ==========
    "docker daemon": {
        "name": "Docker Daemon Not Running",
        "category": "DevOps",
        "root_cause": "Docker 守护进程未运行",
        "solutions": [
            "启动 Docker 服务",
            "检查 Docker 权限",
            "重启 Docker"
        ],
        "fix_code": {
            "template": "# 启动 Docker (Linux)\nsudo systemctl start docker\nsudo systemctl enable docker\n\n# 添加用户到 docker 组\nsudo usermod -aG docker $USER"
        },
        "prevention": ["使用 docker-compose", "检查 Docker 状态"]
    },
    "no space left": {
        "name": "No Space Left on Device",
        "category": "DevOps",
        "root_cause": "磁盘空间不足",
        "solutions": [
            "清理 Docker 缓存",
            "删除未使用的镜像",
            "清理日志文件"
        ],
        "fix_code": {
            "template": "# 清理 Docker\ndocker system prune -a\n\n# 清理日志\nsudo journalctl --vacuum-time=7d\n\n# 检查磁盘使用\ndf -h"
        },
        "prevention": ["设置日志轮转", "使用存储卷"]
    },
    # ========== Git ==========
    "detached head": {
        "name": "Detached HEAD",
        "category": "Git",
        "root_cause": "处于分离 HEAD 状态",
        "solutions": [
            "切换到分支",
            "创建新分支保存更改"
        ],
        "fix_code": {
            "template": "# 方法1: 切换回分支\ngit checkout main\n\n# 方法2: 创建新分支保存更改\ngit checkout -b my-fix\ngit commit -am \"save changes\"\ngit checkout main"
        },
        "prevention": ["使用 git checkout -b 创建分支"]
    },
    "failed to push": {
        "name": "Failed to Push",
        "category": "Git",
        "root_cause": "推送失败，可能有远程更改",
        "solutions": [
            "先拉取远程更改",
            "解决冲突后重新推送"
        ],
        "fix_code": {
            "template": "# 拉取并合并\ngit pull origin main\n\n# 如果有冲突，解决后\ngit add .\ngit commit -am \"merge\"\ngit push origin main"
        },
        "prevention": ["频繁拉取", "使用 rebase"]
    },
    # ========== Python ==========
    "nameerror": {
        "name": "NameError",
        "category": "Python",
        "root_cause": "使用了未定义的名称",
        "solutions": [
            "检查变量名拼写",
            "确认变量已赋值",
            "检查导入是否正确"
        ],
        "fix_code": {
            "template": "# 修复前\nprnt(x)\n\n# 修复后\nprint(x)",
        },
        "prevention": ["使用 IDE", "启用拼写检查"]
    },
    "indentationerror": {
        "name": "IndentationError",
        "category": "Python",
        "root_cause": "缩进错误",
        "solutions": [
            "统一使用空格或 Tab",
            "检查缩进级别",
            "使用 IDE 格式化"
        ],
        "fix_code": {
            "template": "# 使用 4 个空格缩进\ndef my_function():\n    x = 1\n    return x"
        },
        "prevention": ["使用 Black 格式化", "设置 IDE"]
    },
    "filenotfounderror": {
        "name": "FileNotFoundError",
        "category": "Python",
        "root_cause": "文件不存在",
        "solutions": [
            "检查文件路径",
            "使用绝对路径",
            "检查工作目录"
        ],
        "fix_code": {
            "template": "import os\n\n# 检查文件是否存在\nif os.path.exists('file.txt'):\n    with open('file.txt') as f:\n        content = f.read()\nelse:\n    print('File not found')"
        },
        "prevention": ["使用 os.path.exists", "使用 pathlib"]
    },
    "permissionerror": {
        "name": "PermissionError",
        "category": "Python",
        "root_cause": "权限不足",
        "solutions": [
            "检查文件权限",
            "使用 sudo (Linux)",
            "更改文件所有者"
        ],
        "fix_code": {
            "template": "# 更改文件权限 (Linux/Mac)\nchmod 644 file.txt\n\n# 或使用 sudo\nimport subprocess\nsubprocess.run(['sudo', 'chmod', '777', 'file.txt'])"
        },
        "prevention": ["使用合适的权限", "避免 sudo"]
    },
    # ========== JavaScript/Node ==========
    "eacces": {
        "name": "EACCES (Permission Denied)",
        "category": "Node.js",
        "root_cause": "权限被拒绝",
        "solutions": [
            "使用 sudo 安装全局包",
            "配置 npm prefix",
            "使用 nvm"
        ],
        "fix_code": {
            "template": "# 方法1: 使用 nvm\ncurl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash\nnvm install node\n\n# 方法2: 配置 npm\nmkdir ~/.npm-global\nnpm config set prefix '~/.npm-global'\nexport PATH=~/.npm-global/bin:$PATH"
        },
        "prevention": ["使用 nvm", "避免 sudo npm"]
    },
    "ebusy": {
        "name": "EBUSY (File Busy)",
        "category": "Node.js",
        "root_cause": "文件被占用",
        "solutions": [
            "关闭占用文件的程序",
            "重启 Node 进程",
            "检查文件句柄"
        ],
        "fix_code": {
            "template": "# 关闭占用进程\n# Windows\ntaskkill /F /IM node.exe\n\n# Linux/Mac\npkill -f node\n\n# 或等待文件释放"
        },
        "prevention": ["正确关闭文件", "使用 try-finally"]
    },
    # ========== MongoDB ==========
    "mongo network": {
        "name": "MongoDB Network Error",
        "category": "Database",
        "root_cause": "MongoDB 连接错误",
        "solutions": [
            "检查 MongoDB 服务状态",
            "检查连接字符串",
            "检查防火墙"
        ],
        "fix_code": {
            "template": "# MongoDB 连接示例\nfrom pymongo import MongoClient\n\nclient = MongoClient(\n    'mongodb://localhost:27017/',\n    serverSelectionTimeoutMS=5000\n)\n\ntry:\n    client.server_info()\nexcept Exception as e:\n    print(f'Connection failed: {e}')"
        },
        "prevention": ["使用连接池", "添加超时"]
    },
    # ========== Redis ==========
    "redis connection": {
        "name": "Redis Connection Error",
        "category": "Database",
        "root_cause": "Redis 连接失败",
        "solutions": [
            "检查 Redis 服务",
            "检查连接配置",
            "检查内存限制"
        ],
        "fix_code": {
            "template": "import redis\n\nr = redis.Redis(\n    host='localhost',\n    port=6379,\n    socket_connect_timeout=5,\n    socket_timeout=5\n)\n\ntry:\n    r.ping()\nexcept redis.ConnectionError as e:\n    print(f'Connection failed: {e}')"
        },
        "prevention": ["使用连接池", "添加重试"]
    },
    # ========== MySQL ==========
    "mysql access denied": {
        "name": "MySQL Access Denied",
        "category": "Database",
        "root_cause": "MySQL 权限不足",
        "solutions": [
            "检查用户名密码",
            "检查用户权限",
            "检查主机限制"
        ],
        "fix_code": {
            "template": "# 授予权限\nGRANT ALL PRIVILEGES ON database.* TO 'user'@'localhost';\nFLUSH PRIVILEGES;\n\n# Python 连接\nimport pymysql\nconn = pymysql.connect(\n    host='localhost',\n    user='user',\n    password='password',\n    database='mydb'\n)"
        },
        "prevention": ["最小权限原则", "使用环境变量"]
    },
    # ========== PostgreSQL ==========
    "psql invalid input": {
        "name": "PostgreSQL Invalid Input",
        "category": "Database",
        "root_cause": "SQL 语法或参数错误",
        "solutions": [
            "检查 SQL 语法",
            "转义特殊字符",
            "使用参数化查询"
        ],
        "fix_code": {
            "template": "# 使用参数化查询 (防止 SQL 注入)\ncursor.execute(\n    \"INSERT INTO users (name) VALUES (%s)\",\n    (user_input,)\n)\n\n# 而非\ncursor.execute(f\"INSERT INTO users (name) VALUES ('{user_input}')\")"
        },
        "prevention": ["使用参数化查询", "使用 ORM"]
    },

    # ========== Next.js ==========
    "nextjs getserverprops": {
        "name": "Next.js getServerProps Error",
        "category": "Next.js",
        "root_cause": "getServerProps 不能在客户端使用",
        "solutions": [
            "确保在 pages 目录或 getServerSideProps",
            "使用 getStaticProps 配合 revalidate 实现 ISR",
            "检查组件是否标记为 'use client'"
        ],
        "fix_code": {
            "template": "# 使用 getServerSideProps\nexport async function getServerSideProps(context) {\n    const data = await fetchData();\n    return { props: { data } };\n}"
        },
        "prevention": ["理解 Next.js 数据获取方法", "使用 TypeScript"]
    },
    "nextjs hydration": {
        "name": "Next.js Hydration Error",
        "category": "Next.js",
        "root_cause": "服务端和客户端渲染不一致",
        "solutions": [
            "检查是否在渲染时使用了浏览器特有 API",
            "使用 useEffect 在客户端执行",
            "使用 dynamic 导入避免 SSR"
        ],
        "fix_code": {
            "template": "# 使用 dynamic 导入避免 SSR\nimport dynamic from 'next/dynamic';\n\nconst ClientOnly = dynamic(() => import('./ClientOnly'), {\n    ssr: false\n});"
        },
        "prevention": ["避免在 render 中使用 window/document", "使用 useEffect"]
    },

    # ========== NestJS ==========
    "nestjs circular": {
        "name": "NestJS Circular Dependency",
        "category": "NestJS",
        "root_cause": "模块循环依赖",
        "solutions": [
            "使用 forwardRef() 解决循环依赖",
            "重构模块结构",
            "使用属性装饰器代替构造函数注入"
        ],
        "fix_code": {
            "template": "# 使用 forwardRef\nimport { forwardRef } from '@nestjs/common';\n\n@Module({\n    imports: [forwardRef(() => AuthModule)]\n})\nexport class UserModule {}"
        },
        "prevention": ["合理设计模块结构", "使用模块化设计"]
    },
    "nestjs injection": {
        "name": "NestJS Injection Error",
        "category": "NestJS",
        "root_cause": "依赖注入配置错误",
        "solutions": [
            "检查模块是否正确导入",
            "检查 provider 是否在 providers 数组中",
            "检查注入的 token 是否正确"
        ],
        "fix_code": {
            "template": "# 正确配置依赖注入\n@Injectable()\nexport class UserService {\n    constructor(\n        @InjectRepository(User)\n        private userRepository: Repository<User>\n    ) {}\n}"
        },
        "prevention": ["使用 @Injectable() 装饰器", "正确导入模块"]
    },

    # ========== FastAPI ==========
    "fastapi pydantic": {
        "name": "FastAPI Pydantic Error",
        "category": "FastAPI",
        "root_cause": "Pydantic 模型验证失败",
        "solutions": [
            "检查请求体字段类型",
            "使用 Field 设置验证规则",
            "使用 Optional 处理可选字段"
        ],
        "fix_code": {
            "template": "from pydantic import BaseModel, Field\nfrom typing import Optional\n\nclass User(BaseModel):\n    name: str = Field(..., min_length=1)\n    age: Optional[int] = None\n    email: str"
        },
        "prevention": ["使用 Pydantic v2", "添加类型提示"]
    },
    "fastapi coroutine": {
        "name": "FastAPI Coroutine Error",
        "category": "FastAPI",
        "root_cause": "异步函数使用不当",
        "solutions": [
            "使用 async def 定义异步路由",
            "使用 await 调用异步函数",
            "同步函数使用 run_in_executor"
        ],
        "fix_code": {
            "template": "# 异步路由\n@app.get('/items/')\nasync def read_items():\n    return await fetch_items()\n\n# 同步函数在线程池运行\nimport concurrent.futures\n\ndef sync_function():\n    return blocking_io()\n\n@app.get('/sync')\nasync def sync_route():\n    loop = asyncio.get_event_loop()\n    return await loop.run_in_executor(None, sync_function)"
        },
        "prevention": ["区分同步/异步函数", "避免在 async 中使用阻塞调用"]
    },

    # ========== Go ==========
    "go nil pointer": {
        "name": "Go Nil Pointer",
        "category": "Go",
        "root_cause": "空指针异常",
        "solutions": [
            "检查指针是否已初始化",
            "使用 nil 检查",
            "使用 defer recover() 捕获 panic"
        ],
        "fix_code": {
            "template": "// 安全的指针访问\nfunc safeAccess(ptr *MyType) string {\n    if ptr == nil {\n        return \"\"\n    }\n    return ptr.Field\n}\n\n// 使用 recover 捕获 panic\nfunc safeCall(fn func()) {\n    defer func() {\n        if r := recover(); r != nil {\n            fmt.Println(\"Recovered:\", r)\n        }\n    }()\n    fn()\n}"
        },
        "prevention": ["初始化指针", "使用 nil 检查"]
    },
    "go concurrent map": {
        "name": "Go Concurrent Map Access",
        "category": "Go",
        "root_cause": "并发访问 map 不安全",
        "solutions": [
            "使用 sync.RWMutex 保护 map",
            "使用 sync.Map",
            "使用 channel 进行同步"
        ],
        "fix_code": {
            "template": "# 使用 sync.RWMutex\nimport \"sync\"\n\ntype SafeMap struct {\n    mu sync.RWMutex\n    m  map[string]int\n}\n\nfunc (s *SafeMap) Get(key string) int {\n    s.mu.RLock()\n    defer s.mu.RUnlock()\n    return s.m[key]\n}\n\nfunc (s *SafeMap) Set(key string, value int) {\n    s.mu.Lock()\n    defer s.mu.Unlock()\n    s.m[key] = value\n}"
        },
        "prevention": ["使用 sync.Map", "使用 mutex 保护共享资源"]
    },

    # ========== Rust ==========
    "rust borrow": {
        "name": "Rust Borrow Checker Error",
        "category": "Rust",
        "root_cause": "借用检查错误",
        "solutions": [
            "理解所有权和借用规则",
            "使用引用 (&) 而不是可变借用",
            "使用 Clone 复制数据"
        ],
        "fix_code": {
            "template": "// 正确的借用\nfn sum(vec: &Vec<i32>) -> i32 {\n    vec.iter().sum()\n}\n\n// 或者使用生命周期\nfn longest<'a>(x: &'a str, y: &'a str) -> &'a str {\n    if x.len() > y.len() { x } else { y }\n}"
        },
        "prevention": ["学习 Rust 所有权系统", "使用 clippy"]
    },
    "rust unwrap": {
        "name": "Rust Unwrap Error",
        "category": "Rust",
        "root_cause": "使用 unwrap 导致 panic",
        "solutions": [
            "使用 ? 运算符处理 Result",
            "使用 if let/match 处理 Option",
            "使用 unwrap_or 提供默认值"
        ],
        "fix_code": {
            "template": "// 使用 ? 处理 Result\nfn read_file(path: &str) -> Result<String, io::Error> {\n    let mut file = File::open(path)?;\n    let mut contents = String::new();\n    file.read_to_string(&mut contents)?;\n    Ok(contents)\n}\n\n// 使用 unwrap_or 提供默认值\nlet value = optional_value.unwrap_or(default_value);"
        },
        "prevention": ["避免 unwrap/expect", "正确处理错误类型"]
    },

    # ========== Vue 3 ==========
    "vue3 reactivity": {
        "name": "Vue3 Reactivity Warning",
        "category": "Vue",
        "root_cause": "响应式数据修改问题",
        "solutions": [
            "使用 ref/reactive 创建响应式数据",
            "使用 shallowRef 处理大数据",
            "避免直接修改数组索引"
        ],
        "fix_code": {
            "template": "# 使用 ref/reactive\nimport { ref, reactive } from 'vue'\n\n// 基本类型用 ref\nconst count = ref(0)\ncount.value++\n\n// 对象用 reactive\nconst state = reactive({\n    user: null\n})\nstate.user = { name: 'test' }\n\n// 数组修改用 push/splice\nitems.push(newItem)\nitems.splice(index, 1, newItem)"
        },
        "prevention": ["使用 composition API", "遵循 Vue3 响应式规则"]
    },

    # ========== TypeScript ==========
    "typescript error": {
        "name": "TypeScript Compilation Error",
        "category": "TypeScript",
        "root_cause": "TypeScript 类型检查失败",
        "solutions": [
            "检查类型定义是否正确",
            "使用类型断言或类型守卫",
            "添加类型注解",
            "检查泛型类型参数"
        ],
        "fix_code": {
            "template": "// 类型注解\nconst name: string = 'hello';\n\n// 接口定义\ninterface User {\n    name: string;\n    age?: number;\n}\n\n// 类型守卫\nfunction isString(value: unknown): value is string {\n    return typeof value === 'string';\n}"
        },
        "prevention": ["启用 strict 模式", "使用 TypeScript ESLint"]
    },
    "typescript generic": {
        "name": "TypeScript Generic Error",
        "category": "TypeScript",
        "root_cause": "泛型类型不匹配",
        "solutions": [
            "检查泛型类型参数",
            "使用 extends 约束泛型",
            "指定具体类型参数"
        ],
        "fix_code": {
            "template": "// 使用 extends 约束\nfunction getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {\n    return obj[key];\n}"
        },
        "prevention": ["理解泛型约束", "添加类型测试"]
    },

    # ========== Python ==========
    "python none": {
        "name": "Python NoneType Error",
        "category": "Python",
        "root_cause": "对 None 值进行操作",
        "solutions": [
            "使用 if value is not None 检查",
            "使用 Optional 类型提示",
            "使用空值合并 ??"
        ],
        "fix_code": {
            "template": "# 检查 None\nif value is not None:\n    value.do_something()\n\n# 使用 Optional\nfrom typing import Optional\ndef process(value: Optional[str]) -> None:\n    if value:\n        print(value.upper())"
        },
        "prevention": ["使用 Optional 类型", "添加 None 检查"]
    },
    "python recursion": {
        "name": "RecursionError",
        "category": "Python",
        "root_cause": "递归深度超出限制",
        "solutions": [
            "检查递归终止条件",
            "使用迭代代替递归",
            "增加递归深度限制"
        ],
        "fix_code": {
            "template": "# 使用迭代代替递归\ndef fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n\n# 或增加递归限制（不推荐）\nimport sys\nsys.setrecursionlimit(10000)"
        },
        "prevention": ["使用迭代", "添加递归深度检查"]
    },

    # ========== Spring Boot ==========
    "spring autowire": {
        "name": "Spring Autowire Error",
        "category": "Spring",
        "root_cause": "依赖注入失败",
        "solutions": [
            "检查 @Autowired 注解",
            "确认 Bean 已注册",
            "使用构造器注入"
        ],
        "fix_code": {
            "template": "// 使用构造器注入\n@Service\npublic class UserService {\n    private final UserRepository userRepository;\n\n    @Autowired\n    public UserService(UserRepository userRepository) {\n        this.userRepository = userRepository;\n    }\n}"
        },
        "prevention": ["使用构造器注入", "添加 @ComponentScan"]
    },
    "spring null bean": {
        "name": "Spring NoSuchBeanDefinitionException",
        "category": "Spring",
        "root_cause": "Bean 未找到",
        "solutions": [
            "检查 Bean 是否已注册",
            "确认包扫描路径",
            "检查 Bean 名称"
        ],
        "fix_code": {
            "template": "// 添加组件扫描\n@SpringBootApplication\n@ComponentScan(basePackages = {\"com.example.*\"})\npublic class Application {}\n\n// 或添加 Bean\n@Bean\npublic MyService myService() {\n    return new MyService();\n}"
        },
        "prevention": ["明确包扫描", "使用构造器注入"]
    },

    # ========== Django ==========
    "django migration": {
        "name": "Django Migration Error",
        "category": "Django",
        "root_cause": "数据库迁移问题",
        "solutions": [
            "运行 python manage.py makemigrations",
            "运行 python manage.py migrate",
            "检查模型定义"
        ],
        "fix_code": {
            "template": "# 生成迁移\npython manage.py makemigrations\n\n# 执行迁移\npython manage.py migrate\n\n# 查看迁移状态\npython manage.py showmigrations"
        },
        "prevention": ["频繁提交迁移", "测试环境先验证"]
    },
    "django query": {
        "name": "Django QuerySet Error",
        "category": "Django",
        "root_cause": "查询集使用不当",
        "solutions": [
            "检查 QuerySet 是否已求值",
            "使用 filter().first() 代替 filter()[0]",
            "使用 exists() 检查是否存在"
        ],
        "fix_code": {
            "template": "# 错误用法\nuser = User.objects.filter(name='test')[0]\n\n# 正确用法\nuser = User.objects.filter(name='test').first()\n\n# 检查存在\nif User.objects.filter(name='test').exists():\n    pass"
        },
        "prevention": ["使用 first()", "使用 exists()"]
    },

    # ========== Vite ==========
    "vite error": {
        "name": "Vite Build Error",
        "category": "Vite",
        "root_cause": "Vite 构建错误",
        "solutions": [
            "检查 vite.config.js 配置",
            "运行 npm run dev 查看详细错误",
            "清除缓存 rm -rf node_modules/.vite"
        ],
        "fix_code": {
            "template": "# 清除缓存\nrm -rf node_modules/.vite\n\n# 重新安装\nnpm install\n\n# 开发模式\nnpm run dev"
        },
        "prevention": ["定期清理缓存", "检查配置"]
    },

    # ========== Tailwind CSS ==========
    "tailwind not working": {
        "name": "Tailwind CSS Not Working",
        "category": "CSS",
        "root_cause": "Tailwind CSS 未生效",
        "solutions": [
            "运行 npx tailwindcss init",
            "检查 content 配置",
            "重新构建"
        ],
        "fix_code": {
            "template": "# 初始化\nnpx tailwindcss init\n\n# tailwind.config.js\nmodule.exports = {\n  content: [\n    \"./index.html\",\n    \"./src/**/*.{js,jsx,ts,tsx}\",\n  ],\n  theme: {},\n  plugins: [],\n}"
        },
        "prevention": ["正确配置 content", "使用 PostCSS"]
    },

    # ========== Jest ==========
    "jest not found": {
        "name": "Jest Module Not Found",
        "category": "Testing",
        "root_cause": "Jest 找不到模块",
        "solutions": [
            "检查 jest.config.js 配置",
            "安装缺失的依赖",
            "检查模块路径别名"
        ],
        "fix_code": {
            "template": "# jest.config.js\nmodule.exports = {\n  moduleNameMapper: {\n    '^@/(.*)$': '<rootDir>/src/$1'\n  },\n  transform: {\n    '^.+\\\\.(js|jsx|ts|tsx)$': 'babel-jest'\n  }\n}"
        },
        "prevention": ["正确配置 moduleNameMapper", "使用 ts-jest"]
    },

    # ========== Java 常见错误 ==========
    "java nullpointer": {
        "name": "NullPointerException",
        "category": "Java",
        "root_cause": "对 null 值进行操作",
        "solutions": [
            "使用 Objects.requireNonNull() 检查",
            "使用 Optional 处理可能为空的值",
            "添加空值检查"
        ],
        "fix_code": {
            "template": "// 使用 Optional\nString name = Optional.ofNullable(user)\n    .map(User::getName)\n    .orElse(\"Unknown\");\n\n// 或使用空值检查\nif (user != null) {\n    user.getName();\n}"
        },
        "prevention": ["使用 Optional", "启用空指针检查"]
    },
    "java array index": {
        "name": "ArrayIndexOutOfBoundsException",
        "category": "Java",
        "root_cause": "数组索引越界",
        "solutions": [
            "检查数组长度",
            "使用循环边界检查",
            "使用 ArrayList 代替数组"
        ],
        "fix_code": {
            "template": "// 安全访问数组\nint[] arr = {1, 2, 3};\nint index = 5;\n\nif (index >= 0 && index < arr.length) {\n    System.out.println(arr[index]);\n} else {\n    System.out.println(\"Index out of bounds\");\n}\n\n// 或使用 ArrayList\nList<Integer> list = new ArrayList<>();\nlist.get(0); // 会抛 IndexOutOfBoundsException"
        },
        "prevention": ["使用 for-each 循环", "使用 ArrayList"]
    },
    "java class not found": {
        "name": "ClassNotFoundException",
        "category": "Java",
        "root_cause": "类路径中找不到指定的类",
        "solutions": [
            "检查类名是否正确",
            "确认 JAR 包已引入",
            "检查类是否在正确的包中"
        ],
        "fix_code": {
            "template": "// 正确的类加载\ntry {\n    Class.forName(\"com.example.MyClass\");\n} catch (ClassNotFoundException e) {\n    e.printStackTrace();\n    // 检查:\n    // 1. 类名是否正确\n    // 2. JAR 包是否在 classpath 中\n    // 3. 包名是否正确\n}"
        },
        "prevention": ["使用 Maven/Gradle 管理依赖", "检查类路径"]
    },
    "java no such method": {
        "name": "NoSuchMethodException",
        "category": "Java",
        "root_cause": "找不到指定的方法",
        "solutions": [
            "检查方法名拼写",
            "检查方法签名是否正确",
            "确认类版本是否匹配"
        ],
        "fix_code": {
            "template": "// 检查方法签名\ntry {\n    Method method = clazz.getMethod(\"methodName\", String.class, int.class);\n} catch (NoSuchMethodException e) {\n    // 检查:\n    // 1. 方法名是否正确\n    // 2. 参数类型是否匹配\n    // 3. 方法是否存在\n}"
        },
        "prevention": ["使用 IDE 自动补全", "检查 API 文档"]
    },
    "java concurrent modification": {
        "name": "ConcurrentModificationException",
        "category": "Java",
        "root_cause": "在遍历集合时修改集合",
        "solutions": [
            "使用 Iterator 的 remove() 方法",
            "使用 CopyOnWriteArrayList",
            "先复制再遍历"
        ],
        "fix_code": {
            "template": "// 错误写法\nfor (String item : list) {\n    if (item.equals(\"test\")) {\n        list.remove(item); // 抛异常\n    }\n}\n\n// 正确写法 1: 使用 Iterator\nIterator<String> it = list.iterator();\nwhile (it.hasNext()) {\n    if (it.next().equals(\"test\")) {\n        it.remove();\n    }\n}\n\n// 正确写法 2: 使用 CopyOnWriteArrayList\nCopyOnWriteArrayList<String> safeList = new CopyOnWriteArrayList<>(list);"
        },
        "prevention": ["使用 Iterator", "使用线程安全集合"]
    },
    "java out of memory": {
        "name": "OutOfMemoryError",
        "category": "Java",
        "root_cause": "内存不足",
        "solutions": [
            "增加堆内存大小 -Xmx",
            "检查内存泄漏",
            "优化数据结构",
            "使用流处理大数据"
        ],
        "fix_code": {
            "template": "# 增加堆内存\njava -Xmx2g -Xms512m MyApp\n\n# 代码优化: 使用流处理\n// 不要一次性加载所有数据\ntry (Stream<String> lines = Files.lines(Paths.get(\"file.txt\"))) {\n    lines.forEach(line -> process(line));\n}\n\n// 使用缓存限制大小\nLoadingCache<Key, Graph> cache = CacheBuilder.newBuilder()\n    .maximumSize(10000)\n    .build(\n        new CacheLoader<Key, Graph>() {\n            public Graph load(Key key) { return createGraph(key); }\n        });"
        },
        "prevention": ["合理设置堆大小", "避免内存泄漏", "使用缓存"]
    },
    "java stack overflow": {
        "name": "StackOverflowError",
        "category": "Java",
        "root_cause": "栈溢出，通常是递归没有正确终止",
        "solutions": [
            "检查递归终止条件",
            "使用迭代代替递归",
            "增加栈大小 -Xss"
        ],
        "fix_code": {
            "template": "# 增加栈大小\njava -Xss2m MyApp\n\n// 使用迭代代替递归\n// 错误\nint factorial(int n) {\n    return n * factorial(n - 1); // 可能 StackOverflow\n}\n\n// 正确\nint factorial(int n) {\n    int result = 1;\n    for (int i = 2; i <= n; i++) {\n        result *= i;\n    }\n    return result;\n}"
        },
        "prevention": ["使用迭代", "添加递归深度限制"]
    },
    "java illegal argument": {
        "name": "IllegalArgumentException",
        "category": "Java",
        "root_cause": "方法收到非法参数",
        "solutions": [
            "检查参数是否为空",
            "检查参数范围",
            "使用断言验证参数"
        ],
        "fix_code": {
            "template": "// 使用 Objects.requireNonNull\npublic void setName(String name) {\n    this.name = Objects.requireNonNull(name, \"name cannot be null\");\n}\n\n// 使用断言\nassert value >= 0 : \"Value must be positive\";"
        },
        "prevention": ["参数校验", "使用断言"]
    },
    "java illegal state": {
        "name": "IllegalStateException",
        "category": "Java",
        "root_cause": "对象状态不允许当前操作",
        "solutions": [
            "检查对象是否已初始化",
            "检查是否在正确状态下调用方法",
            "按正确顺序调用方法"
        ],
        "fix_code": {
            "template": "// 检查状态\nprivate boolean initialized = false;\n\npublic void doSomething() {\n    if (!initialized) {\n        throw new IllegalStateException(\"Please initialize first\");\n    }\n    // do something\n}\n\npublic void initialize() {\n    // init\n    this.initialized = true;\n}"
        },
        "prevention": ["状态机模式", "按正确顺序调用"]
    },
    "java class cast": {
        "name": "ClassCastException",
        "category": "Java",
        "root_cause": "类型转换失败",
        "solutions": [
            "使用 instanceof 检查类型",
            "使用泛型",
            "使用 Optional 处理"
        ],
        "fix_code": {
            "template": "// 使用 instanceof 检查\nif (obj instanceof String) {\n    String str = (String) obj;\n}\n\n// 使用泛型\nList<String> list = new ArrayList<>();\n\n// 使用模式匹配 (Java 16+)\nif (obj instanceof String s) {\n    System.out.println(s.toLowerCase());\n}"
        },
        "prevention": ["使用泛型", "使用 instanceof"]
    },
    "java number format": {
        "name": "NumberFormatException",
        "category": "Java",
        "root_cause": "字符串转数字格式错误",
        "solutions": [
            "使用 try-catch 捕获",
            "使用正则验证格式",
            "使用 NumberUtils"
        ],
        "fix_code": {
            "template": "// 安全解析数字\npublic static int parseIntSafe(String s) {\n    try {\n        return Integer.parseInt(s);\n    } catch (NumberFormatException e) {\n        return 0; // 或返回 Optional\n    }\n}\n\n// 使用正则验证\nif (s.matches(\"\\\\d+\")) {\n    int num = Integer.parseInt(s);\n}\n\n// 使用 Apache Commons\nint num = NumberUtils.toInt(s, 0);"
        },
        "prevention": ["先验证再解析", "使用工具类"]
    },
    "java no such element": {
        "name": "NoSuchElementException",
        "category": "Java",
        "root_cause": "集合为空时访问",
        "solutions": [
            "使用 hasNext() 检查",
            "使用 Optional",
            "使用默认值"
        ],
        "fix_code": {
            "template": "// 使用 hasNext 检查\nIterator<String> it = list.iterator();\nif (it.hasNext()) {\n    String item = it.next();\n}\n\n// 使用 Optional\nOptional<String> first = list.stream().findFirst();\nString item = first.orElse(\"default\");"
        },
        "prevention": ["先检查再访问", "使用 Optional"]
    },
    "java io exception": {
        "name": "IOException",
        "category": "Java",
        "root_cause": "IO 操作失败",
        "solutions": [
            "检查文件路径",
            "检查文件权限",
            "使用 try-with-resources"
        ],
        "fix_code": {
            "template": "// 使用 try-with-resources\ntry (BufferedReader br = new BufferedReader(new FileReader(\"file.txt\"))) {\n    String line;\n    while ((line = br.readLine()) != null) {\n        System.out.println(line);\n    }\n} catch (IOException e) {\n    e.printStackTrace();\n}\n\n// 检查文件是否存在\nFile file = new File(\"file.txt\");\nif (!file.exists()) {\n    // 处理文件不存在\n}"
        },
        "prevention": ["使用 try-with-resources", "检查文件存在"]
    },
    "java util concurrent": {
        "name": "ExecutionException",
        "category": "Java",
        "root_cause": "线程池执行任务失败",
        "solutions": [
            "检查任务执行异常",
            "使用 Future.get() 捕获异常",
            "检查线程池配置"
        ],
        "fix_code": {
            "template": "// 捕获 ExecutionException\nExecutorService executor = Executors.newFixedThreadPool(10);\nFuture<?> future = executor.submit(() -> {\n    // 任务可能抛异常\n    return doSomething();\n});\n\ntry {\n    Object result = future.get();\n} catch (ExecutionException e) {\n    Throwable cause = e.getCause();\n    cause.printStackTrace(); // 处理根本原因\n}"
        },
        "prevention": ["使用 getCause() 获取真正异常", "合理配置线程池"]
    },
}


# 动态错误模式存储
_DYNAMIC_PATTERNS: Dict[str, Dict] = {}


def add_error_pattern(pattern_key: str, pattern_info: Dict) -> bool:
    """
    动态添加错误模式

    Args:
        pattern_key: 错误模式键名
        pattern_info: 错误信息字典
    """
    global _DYNAMIC_PATTERNS
    if pattern_key in ERROR_DB or pattern_key in _DYNAMIC_PATTERNS:
        logger.warning(f"Pattern {pattern_key} already exists")
        return False

    _DYNAMIC_PATTERNS[pattern_key] = pattern_info
    logger.info(f"Added dynamic error pattern: {pattern_key}")
    return True


def learn_from_case(case: Dict) -> None:
    """
    从排查案例学习，自动添加到错误库

    Args:
        case: 案例字典
    """
    problem = case.get('problem', '').lower()
    error_type = case.get('problem_type', 'unknown')
    root_cause = case.get('root_cause', '')
    solution = case.get('solution', '')
    prevention = case.get('prevention', '')

    if not problem or len(problem) < 10:
        return

    # 提取关键错误类型
    error_name = None
    for name in ['TypeError', 'SyntaxError', 'ReferenceError', 'ValueError', 'Error']:
        if name.lower() in problem:
            error_name = name
            break

    if not error_name:
        error_name = error_type.capitalize() if error_type else "Unknown"

    # 创建新的错误模式
    pattern_key = f"learned_{error_name.lower()}_{hash(problem) % 10000}"
    pattern_info = {
        "name": error_name,
        "category": error_type.capitalize() if error_type else "Learned",
        "root_cause": root_cause or "从案例学习",
        "solutions": [solution] if solution else ["查看具体错误信息"],
        "fix_code": {},
        "prevention": [prevention] if prevention else ["添加输入验证"]
    }

    add_error_pattern(pattern_key, pattern_info)


def get_error_info(error_type: str) -> Optional[Dict]:
    """根据错误类型获取解决方案"""
    error_lower = error_type.lower()

    # 精确匹配
    if error_lower in ERROR_DB:
        return ERROR_DB[error_lower]

    # 模糊匹配
    for key, info in ERROR_DB.items():
        if key in error_lower or info.get('name', '').lower() in error_lower:
            return info

    return None


def get_fix_code(error_type: str) -> Optional[Dict]:
    """获取修复代码示例"""
    info = get_error_info(error_type)
    return info.get('fix_code') if info else None


def search_errors(keyword: str) -> List[Dict]:
    """搜索错误类型"""
    keyword_lower = keyword.lower()
    results = []

    for key, info in ERROR_DB.items():
        if keyword_lower in key or keyword_lower in info.get('name', '').lower():
            results.append({
                'key': key,
                'name': info.get('name'),
                'category': info.get('category')
            })

    return results


def get_all_categories() -> List[str]:
    """获取所有分类"""
    categories = set()
    for info in ERROR_DB.values():
        if 'category' in info:
            categories.add(info['category'])
    return sorted(categories)


def search_by_category(category: str) -> List[Dict]:
    """按分类搜索错误"""
    category_lower = category.lower()
    results = []

    for key, info in ERROR_DB.items():
        if info.get('category', '').lower() == category_lower:
            results.append({
                'key': key,
                'name': info.get('name'),
                'category': info.get('category')
            })

    return results
