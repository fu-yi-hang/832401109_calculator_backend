# 832401109_calculator_backend

## 1. 项目简介

本项目是“前后端分离计算器系统”的后端服务，负责接收前端提交的数学表达式，在服务端完成校验、解析、计算和异常处理，并将每次成功计算的结果持久化到 SQLite 数据库。

核心计算不会在前端完成，也没有使用 `eval()`、`exec()` 或等价的不安全动态执行方式。表达式通过 Python 标准库 `ast` 构建白名单解析器：仅允许数字常量、四则运算、括号以及受限制的一元正负号和部分数学运算符。

## 2. 功能特性

- 支持加、减、乘、除基本运算
- 支持复合表达式、运算符优先级和括号
- 支持小数、一元正数和一元负数
- 拒绝非法表达式、变量名、函数调用和代码注入内容
- 捕获除数为零、数值溢出等异常并返回中文错误信息
- 每次成功计算自动写入 SQLite 历史表
- 提供历史记录查询、单条删除和清空全部历史接口
- 默认返回最近 50 条历史记录，按最新在前排序
- 通过 `flask-cors` 支持跨域前端访问

## 3. 技术栈

| 分类 | 技术 |
|---|---|
| 编程语言 | Python 3.10 或更高版本 |
| Web 框架 | Flask 3.x |
| 跨域支持 | flask-cors |
| 数据库 | SQLite |
| 数据库访问 | Python 标准库 `sqlite3` |
| 表达式解析 | Python 标准库 `ast` 白名单解析 |

## 4. 目录结构

```text
832401109_calculator_backend/
├── app.py              # Flask 服务、表达式解析、SQLite 数据访问和 API 路由
├── requirements.txt    # Python 依赖
├── calculator.db       # SQLite 数据库文件（本地运行或部署后自动生成）
├── README.md           # 项目说明
└── codestyle.md        # 后端代码规范
```

说明：本项目规模较小，采用 Flask 单文件应用形式。`app.py` 内部按注释划分为表达式解析区、数据库区和 API 区，分别对应服务层、模型层和控制器层职责。

## 5. 运行环境

- Python 3.10+
- Windows、macOS 或 Linux
- 网络端口：默认使用 `5000`

## 6. 安装方法

```bash
python -m venv venv
```

激活虚拟环境：

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 7. 启动方法

```bash
python app.py
```

启动成功后，服务默认监听：

```text
http://0.0.0.0:5000
```

本地健康检查：

```bash
curl http://127.0.0.1:5000/
```

预期返回：

```json
{"service":"calculator-backend","status":"running"}
```

## 8. 配置说明

主要配置位于 `app.py`：

| 配置项 | 默认值 | 说明 |
|---|---:|---|
| `DB_PATH` | `app.py` 同目录下的 `calculator.db` | SQLite 数据库位置 |
| `MAX_EXPRESSION_LENGTH` | `200` | 表达式最大长度 |
| `MAX_POWER_EXPONENT` | `1000` | 幂运算指数绝对值上限 |
| 服务地址 | `0.0.0.0:5000` | Flask 监听地址 |
| CORS | 允许全部来源 | 便于 GitHub Pages 等前端访问 |


## 9. 数据库初始化方法

无需手动执行建表脚本。导入或启动 `app.py` 时会自动调用 `init_db()`，创建如下 `history` 表：

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 历史记录 ID |
| `expression` | TEXT | NOT NULL | 原始表达式 |
| `result` | TEXT | NOT NULL | 计算结果，以字符串保存 |
| `created_at` | TEXT | NOT NULL | 计算时间，格式为 `%Y-%m-%d %H:%M:%S` |



## 10. API 一览

| 方法 | 路径 | 功能 | 成功状态码 |
|---|---|---|---:|
| `GET` | `/` | 服务健康检查 | 200 |
| `POST` | `/api/calculate` | 计算表达式并写入历史 | 200 |
| `GET` | `/api/history` | 查询最近 50 条历史 | 200 |
| `DELETE` | `/api/history/<id>` | 删除指定历史记录 | 200 |
| `DELETE` | `/api/history` | 清空全部历史记录 | 200 |

### 10.1 计算接口

请求：

```http
POST /api/calculate
Content-Type: application/json
```

请求体：

```json
{"expression":"(1+2)*3"}
```

成功响应：

```json
{
  "id": 1,
  "expression": "(1+2)*3",
  "result": 9,
  "created_at": "2026-10-06 15:00:00"
}
```

错误响应示例：

```json
{"expression":"1/0","error":"除数不能为零"}
```

```json
{"expression":"abc","error":"表达式包含不允许的内容"}
```

```json
{"error":"表达式不能为空"}
```

### 10.2 查询历史接口

请求：

```http
GET /api/history
```

响应：

```json
{
  "history": [
    {
      "id": 3,
      "expression": "(2+3)*4",
      "result": "20",
      "created_at": "2026-10-06 15:01:00"
    }
  ]
}
```

### 10.3 删除单条历史接口

请求：

```http
DELETE /api/history/3
```

成功响应：

```json
{"id":3,"message":"记录已删除"}
```

记录不存在时返回：

```json
{"error":"记录不存在"}
```

状态码为 `404`。

### 10.4 清空历史接口

请求：

```http
DELETE /api/history
```

响应：

```json
{"message":"历史记录已清空"}
```

## 11. 前端连接方式

前端通过 `API_BASE` 常量访问本服务。本地联调时使用：

```javascript
const API_BASE = "http://127.0.0.1:5000";
```

当前已部署后端地址为：

```text
https://kersied.pythonanywhere.com
```

前端发往该地址的请求示例：

```javascript
await fetch(`${API_BASE}/api/calculate`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({expression: expression})
});
```

## 12. 测试方法

### 12.1 基本计算

```bash
curl -X POST http://127.0.0.1:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression":"12+8"}'
```

### 12.2 复合表达式

```bash
curl -X POST http://127.0.0.1:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression":"(1+2)*3"}'
```

### 12.3 除零异常

```bash
curl -X POST http://127.0.0.1:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"expression":"1/0"}'
```

### 12.4 查询、删除和清空历史

```bash
curl http://127.0.0.1:5000/api/history
curl -X DELETE http://127.0.0.1:5000/api/history/1
curl -X DELETE http://127.0.0.1:5000/api/history
```

## 13. 安全与异常处理说明

- 不直接执行用户输入，不使用 `eval()` 或 `exec()`。
- 只允许 `ast.Constant` 中的整型和浮点型数字。
- 只允许白名单内的二元运算符和一元运算符。
- 函数调用、变量名、属性访问、下标和其他 AST 节点都会被拒绝。
- 限制表达式长度和幂运算指数，降低资源消耗风险。
- 使用参数化 SQL 语句，避免拼接 SQL。
- 已知改进点：极端浮点输入如 `1e309` 可能得到 `Infinity`，建议后续使用 `math.isfinite()` 对结果进行校验。



## 14. 相关仓库

- 前端仓库：<https://github.com/fu-yi-hang/832401109_calculator_frontend>
- 后端仓库：<https://github.com/fu-yi-hang/832401109_calculator_backend>
