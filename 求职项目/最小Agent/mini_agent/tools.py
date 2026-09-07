"""工具注册、Schema 校验和四个小工具，全部使用标准库。"""
import ast
import math
import operator


class ToolError(Exception):
    pass


class Registry:
    def __init__(self):
        self.items = {}

    def register(self, name, description, properties, required, handler):
        if name in self.items:
            raise ValueError("工具名重复：" + name)
        schema = {"type": "object", "properties": properties,
                  "required": required, "additionalProperties": False}
        self.items[name] = ({"type": "function", "function": {
            "name": name, "description": description, "parameters": schema}}, handler)

    def schemas(self):
        return [item[0] for item in self.items.values()]

    def execute(self, name, args, state):
        if name not in self.items:
            raise ToolError("未知工具：" + name)
        definition, handler = self.items[name]
        schema = definition["function"]["parameters"]
        if not isinstance(args, dict):
            raise ToolError("参数必须是 JSON 对象")
        if set(args) - set(schema["properties"]):
            raise ToolError("存在 Schema 未声明的参数")
        if set(schema["required"]) - set(args):
            raise ToolError("缺少必填参数")
        # 当前工具只需要 string/integer/enum；不是完整 JSON Schema 实现。
        for key, value in args.items():
            rule = schema["properties"][key]
            if rule["type"] == "string" and (not isinstance(value, str) or not value.strip()
                                            or len(value) > rule.get("maxLength", 500)):
                raise ToolError(key + " 必须是非空且长度合法的字符串")
            if rule["type"] == "integer" and type(value) is not int:
                raise ToolError(key + " 必须是整数")
            if "enum" in rule and value not in rule["enum"]:
                raise ToolError(key + " 不在允许的枚举值内")
        return handler(args, state)


def calculator(args, state):
    """只解释数字和算术 AST，绝不使用 eval。"""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            result = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            result = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.BinOp) and type(node.op) in ops:
            result = ops[type(node.op)](visit(node.left), visit(node.right))
        else:
            raise ToolError("仅支持数字、括号和 + - * / // %；不支持函数、变量和幂")
        if abs(result) > 1e15 or not math.isfinite(result):
            raise ToolError("计算结果超出范围")
        return result

    try:
        value = visit(ast.parse(args["expression"], mode="eval").body)
        return {"expression": args["expression"], "value": value}
    except (SyntaxError, ZeroDivisionError, OverflowError, RecursionError):
        raise ToolError("表达式错误、除零或计算超限") from None


SEARCH_DATA = [
    {"title": "Agent 是什么", "text": "Agent 用模型选择行动，程序执行工具，再将结果交给模型，循环到完成。"},
    {"title": "Session 与 Memory", "text": "Session 区分会话；Memory 保存状态和历史摘要，追问时按会话召回。"},
    {"title": "周报写法", "text": "周报可以包含本周完成、遇到的问题、下周计划。"},
]


def search(args, state):
    query = args["query"].lower()
    terms = query.split()
    scored = sorted(SEARCH_DATA, key=lambda row: sum(
        term in (row["title"] + row["text"]).lower() for term in terms), reverse=True)
    hits = [row for row in scored if any(term in (row["title"] + row["text"]).lower()
                                       for term in terms)]
    return {"mock": True, "query": args["query"], "results": hits[:3],
            "note": "本地模拟搜索，仅检索三条演示资料；不是互联网实时搜索。"}


def weather(args, state):
    cities = {"北京": (25, "晴"), "上海": (28, "小雨"), "杭州": (27, "多云")}
    city = args["city"].removesuffix("市")
    if city not in cities:
        raise ToolError("模拟天气仅支持北京、上海、杭州")
    temp, condition = cities[city]
    return {"mock": True, "city": city, "temperature_c": temp, "condition": condition,
            "note": "固定演示数据，不代表今日或任何真实日期的天气。"}


def todo(args, state):
    action = args["action"]
    if action == "add":
        if not args.get("text"):
            raise ToolError("添加待办需要 text")
        if len(state["todos"]) >= 20:
            raise ToolError("演示版每个会话最多保留 20 条待办")
        # 同一内容重复添加不产生重复记录（包括模型重复调用）。
        existing = next((t for t in state["todos"] if t["text"] == args["text"]), None)
        if existing:
            return {"item": existing, "duplicate": True}
        item = {"id": state["next_todo_id"], "text": args["text"], "done": False}
        state["next_todo_id"] += 1
        state["todos"].append(item)
        return {"item": item}
    if action == "done":
        item = next((t for t in state["todos"] if t["id"] == args.get("id")), None)
        if item is None:
            raise ToolError("待办 id 不存在，请先 list")
        item["done"] = True
        return {"item": item}
    return {"items": state["todos"]}


def build_registry():
    registry = Registry()
    text = lambda description, limit=200: {"type": "string", "description": description,
                                          "minLength": 1, "maxLength": limit}
    registry.register("calculator", "执行算术计算，支持 + - * / // % 和括号。",
                      {"expression": text("算术表达式，例如 (12+8)*3")}, ["expression"], calculator)
    registry.register("search", "模拟搜索本地 Agent、Memory、周报资料；英文关键词或中文短词。",
                      {"query": text("搜索关键词，例如 Agent、Memory、周报")}, ["query"], search)
    registry.register("weather", "查询模拟天气，仅支持北京、上海、杭州；不是实时天气。",
                      {"city": text("城市名")}, ["city"], weather)
    registry.register("todo", "管理当前会话待办：add 添加(text 必填)，list 列表，done 完成(id 必填)。",
                      {"action": {"type": "string", "enum": ["add", "list", "done"]},
                       "text": text("待办内容", 100), "id": {"type": "integer"}}, ["action"], todo)
    return registry
