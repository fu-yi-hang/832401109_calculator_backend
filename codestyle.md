# 后端代码规范（codestyle.md）


## 规范来源

本规范以 Python 官方 [**PEP 8 — Style Guide for Python Code**](https://peps.python.org/pep-0008/) 为基础，并结合 Flask Web API、SQLite 参数化查询和本项目的小型单文件结构补充项目规则。若项目规则与 PEP 8 冲突，以本文件列出的项目规则为准。

## 1. 基础格式

1. 使用 UTF-8 编码，文件顶部不写非必要的编码声明。
2. 使用 4 个空格缩进，不使用 Tab。
3. 每行建议不超过 100 个字符；字符串或 URL 确实较长时可适当放宽。
4. 顶层函数和类之间保留两个空行，类内方法之间保留一个空行。
5. 运算符两侧、逗号后、注释符号后保留一个空格。
6. 不使用行尾多余空格。

## 2. 命名

| 对象 | 规则 | 示例 |
|---|---|---|
| 模块 | 小写字母，可用下划线 | `history_service.py` |
| 包 | 短小、全小写 | `services` |
| 函数 / 方法 | `snake_case` | `calculate_expression()` |
| 类 | `PascalCase` | `ExpressionError` |
| 常量 | 全大写加下划线 | `MAX_EXPRESSION_LENGTH` |
| 变量 | `snake_case` | `record_id` |
| 私有内部函数 | 前置单下划线 | `_eval_node()` |

命名必须表达用途，避免 `a`、`b`、`tmp1` 等无意义名称；短循环变量除外。

## 3. 导入

1. 导入顺序依次为：标准库、第三方库、本项目模块。
2. 每组之间保留一个空行。
3. 不使用 `from module import *`。
4. 禁止使用 `eval()`、`exec()` 或等价动态执行方式处理用户输入。
5. 标准库可以满足需求时，不额外引入第三方依赖。

示例：

```python
import ast
import operator
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
```

## 4. 表达式解析

1. 表达式解析必须基于白名单机制，只允许项目明确支持的 AST 节点。
2. 数字常量必须排除 `bool`，因为 `bool` 是 `int` 的子类。
3. 遇到函数调用、变量名、属性访问、下标等非数学节点时必须拒绝。
4. 所有不支持的情况都抛出项目自定义异常，不静默返回默认值。
5. 对指数、长度和可能产生超大结果的表达式设置资源上限。

## 5. 数据库访问

1. 所有 SQL 必须使用参数化语句，禁止拼接用户输入。
2. 写操作后必须及时 `commit()`。
3. 数据库连接使用完毕后必须关闭；后续重构可使用上下文管理器统一处理。
4. 查询结果必须显式转换为字典或其他明确的数据结构后再返回给 API 层。
5. 时间格式在项目中统一为 `YYYY-MM-DD HH:MM:SS`。

示例：

```python
cursor = conn.execute(
    "INSERT INTO history (expression, result, created_at) VALUES (?, ?, ?)",
    (expression, str(result), created_at),
)
conn.commit()
```

## 6. API 层

1. 路由函数只负责参数读取、调用业务逻辑、组织响应，不直接写复杂表达式解析逻辑。
2. 请求体必须通过 `request.get_json(silent=True)` 等方式安全读取。
3. 空值、类型错误、超长输入必须在计算前校验。
4. 成功响应使用稳定的 JSON 字段；错误响应必须包含可读的 `error` 信息。
5. 客户端错误返回 `400`，记录不存在返回 `404`，服务端未预期错误返回 `500`。
6. 不把敏感堆栈、路径、密钥或内部配置返回给前端。

## 7. 异常处理

1. 先捕获项目自定义异常，再捕获具体标准异常，最后才捕获兜底异常。
2. 不允许空 `except:`。
3. 除零、溢出、数值不合法等异常必须转换为前端可理解的中文错误信息。
4. 不应吞掉异常；无法恢复时必须返回明确的错误状态。

