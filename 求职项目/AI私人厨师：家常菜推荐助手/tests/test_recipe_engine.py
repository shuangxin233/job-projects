from app.services.recipe_engine import fallback_recipe_answer


def test_fallback_recipe_answer_mentions_matched_recipe():
    answer = fallback_recipe_answer("我有鸡蛋和番茄")

    assert "番茄炒蛋" in answer
    assert "番茄鸡蛋汤" in answer
    assert "食品安全提醒" in answer
