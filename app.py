"""前后端分离计算器系统 —— 后端服务
Flask + SQLite，使用 ast 白名单机制安全解析并计算表达式。

文件内分区（职责说明）：
  1. 表达式解析区：基于 ast 的白名单解析与安全求值（service 职责）
  2. 数据库区：SQLite 连接、建表与增删查（model 职责）
  3. API 区：Flask 路由、参数校验与响应（controller 职责）
"""
import ast
import operator
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许 GitHub Pages 前端跨域访问

DB_PATH = Path(__file__).parent / "calculator.db"

MAX_EXPRESSION_LENGTH = 200          # 表达式长度上限，防止超长输入
MAX_POWER_EXPONENT = 1000            # 幂运算指数上限，防止 2**999999999 拖垮服务


# ==================== 1. 表达式解析区 ====================
ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
}
ALLOWED_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class ExpressionError(Exception):
    """表达式不合法时抛出，用于向前端返回 400。"""


def evaluate(expression: str):
    """用 ast 白名单解析表达式并安全求值，只放行数字与四则运算节点。"""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise ExpressionError("表达式语法错误")

    def eval_node(node):
        # 叶子：只允许数字常量（拒绝 True/False、字符串等）
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ExpressionError("只允许数字常量")
            return node.value
        # 二元运算：+ - * / % // **
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in ALLOWED_BIN_OPS:
                raise ExpressionError("不支持的运算符")
            left = eval_node(node.left)
            right = eval_node(node.right)
            if op_type is ast.Pow and abs(right) > MAX_POWER_EXPONENT:
                raise ExpressionError("指数过大")
            return ALLOWED_BIN_OPS[op_type](left, right)
        # 一元运算：正负号
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in ALLOWED_UNARY_OPS:
                raise ExpressionError("不支持的一元运算符")
            return ALLOWED_UNARY_OPS[op_type](eval_node(node.operand))
        # 其余节点（函数调用、变量名、属性、下标……）一律拒绝
        raise ExpressionError("表达式包含不允许的内容")

    return eval_node(tree.body)


def format_number(value):
    """把 20.0 这类浮点结果格式化为 20，保持输出简洁。"""
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e16:
        return int(value)
    return value


# ==================== 2. 数据库区 ====================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据表（幂等，重复调用安全）。"""
    conn = get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            expression TEXT    NOT NULL,
            result     TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        )"""
    )
    conn.commit()
    conn.close()


# ==================== 3. API 区 ====================
@app.get("/")
def index():
    return jsonify({"service": "calculator-backend", "status": "running"})


@app.post("/api/calculate")
def calculate():
    """接收 {"expression": "12+8"}，返回 {"expression": "12+8", "result": 20}。"""
    data = request.get_json(silent=True) or {}
    expression = str(data.get("expression", "")).strip()

    if not expression:
        return jsonify({"error": "表达式不能为空"}), 400
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return jsonify({"error": "表达式过长"}), 400

    try:
        value = evaluate(expression)
        result = format_number(value)
    except ExpressionError as exc:
        return jsonify({"expression": expression, "error": str(exc)}), 400
    except ZeroDivisionError:
        return jsonify({"expression": expression, "error": "除数不能为零"}), 400
    except (OverflowError, ValueError):
        return jsonify({"expression": expression, "error": "数值超出可计算范围"}), 400

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO history (expression, result, created_at) VALUES (?, ?, ?)",
        (expression, str(result), created_at),
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "id": record_id,
        "expression": expression,
        "result": result,
        "created_at": created_at,
    }), 200


@app.get("/api/history")
def get_history():
    """返回最近 50 条计算历史，最新的在前。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, expression, result, created_at FROM history ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify({"history": [dict(row) for row in rows]})


@app.delete("/api/history/<int:record_id>")
def delete_history(record_id):
    """根据 ID 删除一条历史记录，记录必须真正从数据库删除。"""
    conn = get_db()
    cursor = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if deleted == 0:
        return jsonify({"error": "记录不存在"}), 404
    return jsonify({"message": "记录已删除", "id": record_id})


@app.delete("/api/history")
def clear_history():
    """清空全部计算历史（附加功能）。"""
    conn = get_db()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return jsonify({"message": "历史记录已清空"})


init_db()   # 模块导入时即建表：本地直接运行和 WSGI 部署两种情况都覆盖

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
