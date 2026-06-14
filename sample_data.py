import os
import sys
from datetime import datetime, timedelta

from models import Ingredient, Dish, RecipeItem, PriceHistory
from storage import DataStorage


def create_sample_data():
    print("正在创建示例数据...")

    storage = DataStorage()

    ingredients = {
        "1": Ingredient(
            id="1", name="牛肉", unit="kg", current_price=60.0, calorie_per_unit=2500
        ),
        "2": Ingredient(
            id="2", name="鸡肉", unit="kg", current_price=25.0, calorie_per_unit=1650
        ),
        "3": Ingredient(
            id="3", name="猪肉", unit="kg", current_price=35.0, calorie_per_unit=2420
        ),
        "4": Ingredient(
            id="4", name="洋葱", unit="kg", current_price=5.0, calorie_per_unit=400
        ),
        "5": Ingredient(
            id="5", name="青椒", unit="kg", current_price=8.0, calorie_per_unit=270
        ),
        "6": Ingredient(
            id="6", name="土豆", unit="kg", current_price=4.0, calorie_per_unit=770
        ),
        "7": Ingredient(
            id="7", name="米饭", unit="kg", current_price=3.0, calorie_per_unit=1100
        ),
        "8": Ingredient(
            id="8", name="面条", unit="kg", current_price=6.0, calorie_per_unit=2800
        ),
        "9": Ingredient(
            id="9", name="酱油", unit="L", current_price=12.0, calorie_per_unit=200
        ),
        "10": Ingredient(
            id="10", name="食用油", unit="L", current_price=20.0, calorie_per_unit=9000
        ),
        "11": Ingredient(
            id="11", name="盐", unit="kg", current_price=5.0, calorie_per_unit=0
        ),
        "12": Ingredient(
            id="12", name="可乐", unit="L", current_price=4.0, calorie_per_unit=420
        ),
        "13": Ingredient(
            id="13", name="黄瓜", unit="kg", current_price=6.0, calorie_per_unit=160
        ),
        "14": Ingredient(
            id="14", name="花生米", unit="kg", current_price=15.0, calorie_per_unit=5670
        ),
    }

    base_time = datetime.now()
    price_histories = {
        "1": [52.0, 55.0, 58.0, 60.0],
        "2": [22.0, 23.5, 24.0, 25.0],
        "3": [30.0, 32.0, 34.0, 35.0],
        "10": [18.0, 19.0, 19.5, 20.0],
    }

    for ing_id, prices in price_histories.items():
        ing = ingredients[ing_id]
        ing.price_history = []
        for i, price in enumerate(prices):
            days_ago = (len(prices) - 1 - i) * 7
            ing.price_history.append(
                PriceHistory(
                    price=price,
                    timestamp=base_time - timedelta(days=days_ago)
                )
            )
        ing.current_price = prices[-1]

    dishes = [
        Dish(
            name="洋葱炒牛肉",
            category="热菜",
            target_margin=0.6,
            recipe=[
                RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g"),
                RecipeItem(ingredient_id="4", ingredient_name="洋葱", amount=100, unit="g"),
                RecipeItem(ingredient_id="9", ingredient_name="酱油", amount=15, unit="ml"),
                RecipeItem(ingredient_id="10", ingredient_name="食用油", amount=20, unit="ml"),
                RecipeItem(ingredient_id="11", ingredient_name="盐", amount=2, unit="g"),
            ]
        ),
        Dish(
            name="青椒炒肉丝",
            category="热菜",
            target_margin=0.6,
            recipe=[
                RecipeItem(ingredient_id="2", ingredient_name="鸡肉", amount=150, unit="g"),
                RecipeItem(ingredient_id="5", ingredient_name="青椒", amount=100, unit="g"),
                RecipeItem(ingredient_id="9", ingredient_name="酱油", amount=10, unit="ml"),
                RecipeItem(ingredient_id="10", ingredient_name="食用油", amount=15, unit="ml"),
            ]
        ),
        Dish(
            name="土豆烧肉",
            category="热菜",
            target_margin=0.55,
            recipe=[
                RecipeItem(ingredient_id="3", ingredient_name="猪肉", amount=180, unit="g"),
                RecipeItem(ingredient_id="6", ingredient_name="土豆", amount=150, unit="g"),
                RecipeItem(ingredient_id="9", ingredient_name="酱油", amount=20, unit="ml"),
                RecipeItem(ingredient_id="10", ingredient_name="食用油", amount=15, unit="ml"),
                RecipeItem(ingredient_id="11", ingredient_name="盐", amount=3, unit="g"),
            ]
        ),
        Dish(
            name="凉拌黄瓜",
            category="凉菜",
            target_margin=0.7,
            recipe=[
                RecipeItem(ingredient_id="13", ingredient_name="黄瓜", amount=200, unit="g"),
                RecipeItem(ingredient_id="9", ingredient_name="酱油", amount=10, unit="ml"),
                RecipeItem(ingredient_id="11", ingredient_name="盐", amount=2, unit="g"),
            ]
        ),
        Dish(
            name="油炸花生米",
            category="凉菜",
            target_margin=0.65,
            recipe=[
                RecipeItem(ingredient_id="14", ingredient_name="花生米", amount=100, unit="g"),
                RecipeItem(ingredient_id="10", ingredient_name="食用油", amount=30, unit="ml"),
                RecipeItem(ingredient_id="11", ingredient_name="盐", amount=1, unit="g"),
            ]
        ),
        Dish(
            name="白米饭",
            category="主食",
            target_margin=0.3,
            recipe=[
                RecipeItem(ingredient_id="7", ingredient_name="米饭", amount=200, unit="g"),
            ]
        ),
        Dish(
            name="牛肉面",
            category="主食",
            target_margin=0.5,
            recipe=[
                RecipeItem(ingredient_id="8", ingredient_name="面条", amount=150, unit="g"),
                RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=50, unit="g"),
                RecipeItem(ingredient_id="9", ingredient_name="酱油", amount=10, unit="ml"),
                RecipeItem(ingredient_id="11", ingredient_name="盐", amount=2, unit="g"),
            ]
        ),
        Dish(
            name="可乐",
            category="饮品",
            target_margin=0.7,
            recipe=[
                RecipeItem(ingredient_id="12", ingredient_name="可乐", amount=330, unit="ml"),
            ]
        ),
    ]

    storage.save_ingredients(ingredients)
    storage.save_dishes(dishes)

    print(f"✓ 已创建 {len(ingredients)} 种原材料")
    print(f"✓ 已创建 {len(dishes)} 道菜品")
    print()
    print("原材料清单:")
    for ing in sorted(ingredients.values(), key=lambda x: x.name):
        print(f"  - {ing.name}: {ing.current_price}元/{ing.unit}")
    print()
    print("菜品清单:")
    for dish in dishes:
        print(f"  - {dish.name} ({dish.category}): {len(dish.recipe)}种原材料")
    print()
    print("示例数据创建完成！现在可以运行 python main.py 开始使用。")


if __name__ == "__main__":
    create_sample_data()
