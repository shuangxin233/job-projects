import time

from backend.models.schemas import ChatMessage


SYSTEM_PROMPT = """你是一个面向家庭做饭场景的 AI 私人厨师。
回答要使用中文 Markdown，优先给出可执行、适合新手的做法。
如果用户提供食材图片链接但你无法直接识别图片，请说明需要用户补充食材名称。
输出结构固定为：
1. 识别到的食材或需求
2. 推荐菜谱，包含难度、预计时间、适合原因
3. 制作步骤
4. 调味与替代建议
5. 食品安全提醒
"""


INGREDIENT_RECIPES = {
    "鸡蛋": {
        "title": "番茄炒蛋",
        "difficulty": "入门",
        "time": "15 分钟",
        "reason": "步骤短，失败成本低，适合展示基础烹饪推荐能力。",
        "steps": ["番茄切块，鸡蛋打散加少量盐。", "热锅下蛋液，凝固后盛出。", "炒番茄出汁，再倒回鸡蛋翻炒。"],
        "seasonings": ["盐", "少量糖", "葱花"],
    },
    "番茄": {
        "title": "番茄鸡蛋汤",
        "difficulty": "入门",
        "time": "12 分钟",
        "reason": "适合冰箱常见食材，能体现快速家常菜推荐。",
        "steps": ["番茄切块炒出汁。", "加水煮开后淋入蛋液。", "出锅前加盐和葱花。"],
        "seasonings": ["盐", "白胡椒", "香油"],
    },
    "土豆": {
        "title": "酸辣土豆丝",
        "difficulty": "初级",
        "time": "20 分钟",
        "reason": "刀工和火候都有一点挑战，但仍适合初学者练习。",
        "steps": ["土豆切丝后清水冲掉淀粉。", "热锅爆香蒜末和干辣椒。", "大火快炒，出锅前加醋。"],
        "seasonings": ["盐", "醋", "干辣椒", "蒜"],
    },
    "鸡胸肉": {
        "title": "低脂鸡胸肉蔬菜碗",
        "difficulty": "初级",
        "time": "25 分钟",
        "reason": "能覆盖健康饮食场景，适合求职项目里说明用户价值。",
        "steps": ["鸡胸肉切片，用盐和黑胡椒腌 10 分钟。", "少油煎熟鸡胸肉。", "搭配生菜、玉米或土豆装盘。"],
        "seasonings": ["盐", "黑胡椒", "生抽", "柠檬汁"],
    },
}


def build_ollama_messages(history: list[ChatMessage]) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history[-10:]:
        content = item.content
        if item.image_url:
            content = f"{content}\n\n用户上传的食材图片链接：{item.image_url}"
        messages.append({"role": item.role, "content": content})
    return messages


def fallback_recipe_answer(message: str, image_url: str | None = None) -> str:
    matched = [name for name in INGREDIENT_RECIPES if name in message]
    if not matched:
        matched = ["鸡蛋", "番茄"]

    recipe_blocks = []
    for name in matched[:3]:
        recipe = INGREDIENT_RECIPES[name]
        recipe_blocks.append(
            f"### {recipe['title']}\n"
            f"- 难度：{recipe['difficulty']}\n"
            f"- 预计时间：{recipe['time']}\n"
            f"- 推荐原因：{recipe['reason']}\n"
            f"- 调味：{', '.join(recipe['seasonings'])}\n"
            f"- 步骤：\n"
            + "\n".join(f"  {index}. {step}" for index, step in enumerate(recipe["steps"], start=1))
        )

    image_note = ""
    if image_url:
        image_note = f"\n\n你上传了图片：{image_url}\n当前本地兜底模式不能直接识别图片，请把图片里的食材名称也输入一遍。"

    return (
        "## 私厨推荐\n\n"
        f"我收到的需求是：{message}{image_note}\n\n"
        "下面先按常见家庭食材给出可执行方案：\n\n"
        + "\n\n".join(recipe_blocks)
        + "\n\n## 食品安全提醒\n\n"
        "肉类和蛋类要完全加热；剩菜冷藏后建议 24 小时内吃完。"
        "\n\n> 当前使用的是本地兜底菜谱逻辑。启动 Ollama 并拉取模型后，会自动切换为大模型回答。"
    )


def chunk_text(text: str, size: int = 24):
    for start in range(0, len(text), size):
        yield text[start : start + size]
        time.sleep(0.02)
