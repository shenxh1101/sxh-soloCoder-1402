import unittest
import os
import tempfile
import shutil
from datetime import datetime, timedelta

from models import Ingredient, Dish, RecipeItem, PriceHistory, DishCostAnalysis
from cost_calculator import CostCalculator, MarginAnalyzer
from storage import DataStorage
from csv_importer import CSVImporter
from ascii_chart import AsciiChart


class TestModels(unittest.TestCase):
    def test_price_history(self):
        ph = PriceHistory(price=10.5)
        self.assertEqual(ph.price, 10.5)
        self.assertIsInstance(ph.timestamp, datetime)

        data = ph.to_dict()
        ph2 = PriceHistory.from_dict(data)
        self.assertEqual(ph2.price, 10.5)
        self.assertEqual(ph2.timestamp, ph.timestamp)

    def test_ingredient_creation(self):
        ing = Ingredient(name="牛肉", unit="kg", current_price=60.0, calorie_per_unit=2500)
        self.assertEqual(ing.name, "牛肉")
        self.assertEqual(ing.unit, "kg")
        self.assertEqual(ing.current_price, 60.0)
        self.assertEqual(ing.calorie_per_unit, 2500)
        self.assertEqual(len(ing.price_history), 1)

    def test_ingredient_unit_conversion(self):
        ing = Ingredient(name="牛肉", unit="kg", current_price=60.0)

        self.assertEqual(ing.get_unit_conversion("g", 200), 0.2)
        self.assertEqual(ing.get_unit_conversion("kg", 1), 1.0)
        self.assertEqual(ing.get_unit_conversion("kg", 0.5), 0.5)

        ing_liquid = Ingredient(name="酱油", unit="L", current_price=12.0)
        self.assertEqual(ing_liquid.get_unit_conversion("ml", 1000), 1.0)
        self.assertEqual(ing_liquid.get_unit_conversion("ml", 500), 0.5)

        with self.assertRaises(ValueError):
            ing.get_unit_conversion("invalid", 100)

    def test_ingredient_cost_calculation(self):
        ing = Ingredient(name="牛肉", unit="kg", current_price=60.0)

        cost = ing.calculate_cost(200, "g")
        self.assertAlmostEqual(cost, 12.0, places=2)

        cost = ing.calculate_cost(1, "kg")
        self.assertEqual(cost, 60.0)

    def test_ingredient_calorie_calculation(self):
        ing = Ingredient(name="牛肉", unit="kg", current_price=60.0, calorie_per_unit=2500)

        calorie = ing.calculate_calorie(200, "g")
        self.assertAlmostEqual(calorie, 500, places=0)

        ing_no_calorie = Ingredient(name="盐", unit="kg", current_price=5.0)
        self.assertIsNone(ing_no_calorie.calculate_calorie(100, "g"))

    def test_ingredient_price_update(self):
        ing = Ingredient(name="牛肉", unit="kg", current_price=60.0)
        self.assertEqual(len(ing.price_history), 1)

        ing.update_price(65.0)
        self.assertEqual(ing.current_price, 65.0)
        self.assertEqual(len(ing.price_history), 2)
        self.assertEqual(ing.price_history[1].price, 65.0)

    def test_ingredient_serialization(self):
        ing = Ingredient(name="牛肉", unit="kg", current_price=60.0, calorie_per_unit=2500)
        ing.update_price(65.0)

        data = ing.to_dict()
        ing2 = Ingredient.from_dict(data)

        self.assertEqual(ing2.id, ing.id)
        self.assertEqual(ing2.name, ing.name)
        self.assertEqual(ing2.current_price, ing.current_price)
        self.assertEqual(len(ing2.price_history), 2)

    def test_recipe_item(self):
        item = RecipeItem(ingredient_id="test123", ingredient_name="牛肉", amount=200, unit="g")
        self.assertEqual(item.ingredient_id, "test123")
        self.assertEqual(item.amount, 200)

        data = item.to_dict()
        item2 = RecipeItem.from_dict(data)
        self.assertEqual(item2.ingredient_id, item.ingredient_id)
        self.assertEqual(item2.amount, item.amount)

    def test_dish_creation(self):
        recipe = [
            RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g"),
            RecipeItem(ingredient_id="2", ingredient_name="洋葱", amount=50, unit="g"),
        ]
        dish = Dish(name="洋葱炒牛肉", category="热菜", recipe=recipe, target_margin=0.6)

        self.assertEqual(dish.name, "洋葱炒牛肉")
        self.assertEqual(dish.category, "热菜")
        self.assertEqual(dish.target_margin, 0.6)
        self.assertEqual(len(dish.recipe), 2)

    def test_dish_serialization(self):
        recipe = [
            RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g"),
        ]
        dish = Dish(name="洋葱炒牛肉", category="热菜", recipe=recipe)

        data = dish.to_dict()
        dish2 = Dish.from_dict(data)

        self.assertEqual(dish2.id, dish.id)
        self.assertEqual(dish2.name, dish.name)
        self.assertEqual(len(dish2.recipe), 1)


class TestCostCalculator(unittest.TestCase):
    def setUp(self):
        self.ingredients = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0, calorie_per_unit=2500),
            "2": Ingredient(id="2", name="洋葱", unit="kg", current_price=5.0, calorie_per_unit=400),
            "3": Ingredient(id="3", name="酱油", unit="L", current_price=12.0, calorie_per_unit=200),
            "4": Ingredient(id="4", name="鸡肉", unit="kg", current_price=25.0, calorie_per_unit=1650),
        }

        self.recipe = [
            RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g"),
            RecipeItem(ingredient_id="2", ingredient_name="洋葱", amount=50, unit="g"),
            RecipeItem(ingredient_id="3", ingredient_name="酱油", amount=10, unit="ml"),
        ]

        self.dish = Dish(name="洋葱炒牛肉", category="热菜", recipe=self.recipe, target_margin=0.6)

    def test_calculate_dish_cost(self):
        analysis = CostCalculator.calculate_dish_cost(self.dish, self.ingredients)

        expected_cost = (200/1000)*60 + (50/1000)*5 + (10/1000)*12
        self.assertAlmostEqual(analysis.material_cost, expected_cost, places=2)

        expected_price = expected_cost / (1 - 0.6)
        self.assertAlmostEqual(analysis.suggested_price, expected_price, places=2)

        expected_profit = expected_price - expected_cost
        self.assertAlmostEqual(analysis.gross_profit, expected_profit, places=2)

        expected_margin = expected_profit / expected_price
        self.assertAlmostEqual(analysis.gross_margin, expected_margin, places=4)

        expected_calorie = (200/1000)*2500 + (50/1000)*400 + (10/1000)*200
        self.assertAlmostEqual(analysis.total_calorie, expected_calorie, places=0)

        self.assertEqual(len(analysis.ingredient_costs), 3)

    def test_calculate_dish_cost_invalid_margin(self):
        dish = Dish(name="测试菜", category="热菜", recipe=self.recipe, target_margin=1.0)
        with self.assertRaises(ValueError):
            CostCalculator.calculate_dish_cost(dish, self.ingredients)

    def test_calculate_dish_cost_missing_ingredient(self):
        bad_recipe = [RecipeItem(ingredient_id="999", ingredient_name="未知", amount=100, unit="g")]
        bad_dish = Dish(name="测试菜", category="热菜", recipe=bad_recipe)
        with self.assertRaises(ValueError):
            CostCalculator.calculate_dish_cost(bad_dish, self.ingredients)

    def test_calculate_all_dishes(self):
        dish2 = Dish(name="另一道菜", category="凉菜", recipe=self.recipe, target_margin=0.5)
        analyses = CostCalculator.calculate_all_dishes([self.dish, dish2], self.ingredients)
        self.assertEqual(len(analyses), 2)

    def test_simulate_ingredient_replace(self):
        result = CostCalculator.simulate_ingredient_replace(
            self.dish,
            "1",
            self.ingredients["4"],
            200,
            "g",
            self.ingredients
        )

        self.assertIn('original', result)
        self.assertIn('new', result)
        self.assertIn('cost_diff', result)
        self.assertIn('calorie_diff', result)

        original_cost = result['original'].material_cost
        new_cost = result['new'].material_cost
        self.assertAlmostEqual(result['cost_diff'], new_cost - original_cost, places=2)

        self.assertIsNotNone(result['calorie_diff'])


class TestMarginAnalyzer(unittest.TestCase):
    def setUp(self):
        ingredients = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0),
            "2": Ingredient(id="2", name="蔬菜", unit="kg", current_price=5.0),
        }

        recipe1 = [RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g")]
        recipe2 = [RecipeItem(ingredient_id="2", ingredient_name="蔬菜", amount=300, unit="g")]

        dish1 = Dish(name="高价菜", category="热菜", recipe=recipe1, target_margin=0.7)
        dish2 = Dish(name="低价菜", category="凉菜", recipe=recipe2, target_margin=0.3)
        dish3 = Dish(name="中价菜", category="热菜", recipe=recipe2, target_margin=0.6)

        self.analyses = CostCalculator.calculate_all_dishes([dish1, dish2, dish3], ingredients)

    def test_analyze_by_category(self):
        stats = MarginAnalyzer.analyze_by_category(self.analyses)

        self.assertIn("热菜", stats)
        self.assertIn("凉菜", stats)
        self.assertEqual(stats["热菜"]["count"], 2)
        self.assertEqual(stats["凉菜"]["count"], 1)
        self.assertGreater(stats["热菜"]["avg_margin"], 0)

    def test_get_low_margin_dishes(self):
        low_margin = MarginAnalyzer.get_low_margin_dishes(self.analyses, 0.4)
        self.assertEqual(len(low_margin), 1)
        self.assertEqual(low_margin[0].dish.name, "低价菜")


class TestDataStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = DataStorage(data_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_save_and_load_ingredients(self):
        ingredients = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0),
            "2": Ingredient(id="2", name="洋葱", unit="kg", current_price=5.0),
        }

        self.storage.save_ingredients(ingredients)
        loaded = self.storage.load_ingredients()

        self.assertEqual(len(loaded), 2)
        self.assertIn("1", loaded)
        self.assertEqual(loaded["1"].name, "牛肉")
        self.assertEqual(loaded["1"].current_price, 60.0)

    def test_save_and_load_dishes(self):
        recipe = [RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g")]
        dishes = [Dish(name="测试菜", category="热菜", recipe=recipe)]

        self.storage.save_dishes(dishes)
        loaded = self.storage.load_dishes()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, "测试菜")
        self.assertEqual(len(loaded[0].recipe), 1)

    def test_get_by_name(self):
        ingredients = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0),
        }
        dish = [Dish(name="测试菜", category="热菜", recipe=[])]

        self.assertIsNotNone(self.storage.get_ingredient_by_name("牛肉", ingredients))
        self.assertIsNone(self.storage.get_ingredient_by_name("猪肉", ingredients))
        self.assertIsNotNone(self.storage.get_dish_by_name("测试菜", dish))
        self.assertIsNone(self.storage.get_dish_by_name("不存在", dish))


class TestCSVImporter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ingredients_file = os.path.join(self.test_dir, "ingredients.csv")
        self.dishes_file = os.path.join(self.test_dir, "dishes.csv")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_generate_and_import_ingredients(self):
        CSVImporter.generate_ingredient_template(self.ingredients_file)
        self.assertTrue(os.path.exists(self.ingredients_file))

        ingredients, errors = CSVImporter.import_ingredients(self.ingredients_file)
        self.assertEqual(len(errors), 0)
        self.assertGreater(len(ingredients), 0)
        self.assertEqual(ingredients[0].name, "牛肉")

    def test_generate_and_import_dishes(self):
        existing_ings = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0),
            "2": Ingredient(id="2", name="洋葱", unit="kg", current_price=5.0),
            "3": Ingredient(id="3", name="酱油", unit="L", current_price=12.0),
        }

        CSVImporter.generate_dish_template(self.dishes_file)
        self.assertTrue(os.path.exists(self.dishes_file))

        dishes, errors = CSVImporter.import_dishes(self.dishes_file, existing_ings)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(dishes), 1)
        self.assertEqual(dishes[0].name, "洋葱炒牛肉")
        self.assertEqual(len(dishes[0].recipe), 3)

    def test_import_missing_file(self):
        ingredients, errors = CSVImporter.import_ingredients("nonexistent.csv")
        self.assertEqual(len(ingredients), 0)
        self.assertGreater(len(errors), 0)


class TestAsciiChart(unittest.TestCase):
    def test_draw_line_chart(self):
        now = datetime.now()
        data_points = [
            (now - timedelta(days=5), 50.0),
            (now - timedelta(days=4), 52.0),
            (now - timedelta(days=3), 48.0),
            (now - timedelta(days=2), 55.0),
            (now - timedelta(days=1), 60.0),
        ]

        chart = AsciiChart.draw_line_chart(data_points, title="测试图表")
        self.assertIsInstance(chart, str)
        self.assertIn("测试图表", chart)
        self.assertIn("最低价格", chart)
        self.assertIn("最高价格", chart)

    def test_draw_line_chart_empty(self):
        chart = AsciiChart.draw_line_chart([])
        self.assertEqual(chart, "无数据可显示")

    def test_draw_bar_chart(self):
        data = [
            ("热菜", 65.5),
            ("凉菜", 55.2),
            ("主食", 70.0),
            ("饮品", 45.0),
        ]

        chart = AsciiChart.draw_bar_chart(data, title="测试柱状图")
        self.assertIsInstance(chart, str)
        self.assertIn("测试柱状图", chart)
        self.assertIn("热菜", chart)
        self.assertIn("凉菜", chart)

    def test_draw_bar_chart_empty(self):
        chart = AsciiChart.draw_bar_chart([])
        self.assertEqual(chart, "无数据可显示")


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = DataStorage(data_dir=self.test_dir)

        self.ingredients = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0, calorie_per_unit=2500),
            "2": Ingredient(id="2", name="洋葱", unit="kg", current_price=5.0, calorie_per_unit=400),
            "3": Ingredient(id="3", name="酱油", unit="L", current_price=12.0, calorie_per_unit=200),
            "4": Ingredient(id="4", name="鸡肉", unit="kg", current_price=25.0, calorie_per_unit=1650),
            "5": Ingredient(id="5", name="米饭", unit="kg", current_price=3.0, calorie_per_unit=1100),
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_workflow(self):
        recipe1 = [
            RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g"),
            RecipeItem(ingredient_id="2", ingredient_name="洋葱", amount=50, unit="g"),
            RecipeItem(ingredient_id="3", ingredient_name="酱油", amount=10, unit="ml"),
        ]
        dish1 = Dish(name="洋葱炒牛肉", category="热菜", recipe=recipe1, target_margin=0.6)

        recipe2 = [
            RecipeItem(ingredient_id="5", ingredient_name="米饭", amount=200, unit="g"),
        ]
        dish2 = Dish(name="白米饭", category="主食", recipe=recipe2, target_margin=0.3)

        self.storage.save_ingredients(self.ingredients)
        self.storage.save_dishes([dish1, dish2])

        loaded_ings = self.storage.load_ingredients()
        loaded_dishes = self.storage.load_dishes()

        self.assertEqual(len(loaded_ings), 5)
        self.assertEqual(len(loaded_dishes), 2)

        analyses = CostCalculator.calculate_all_dishes(loaded_dishes, loaded_ings)
        self.assertEqual(len(analyses), 2)

        self.assertAlmostEqual(analyses[0].gross_margin, 0.6, places=4)

        low_margin = MarginAnalyzer.get_low_margin_dishes(analyses, 0.4)
        self.assertEqual(len(low_margin), 1)
        self.assertEqual(low_margin[0].dish.name, "白米饭")

        category_stats = MarginAnalyzer.analyze_by_category(analyses)
        self.assertIn("热菜", category_stats)
        self.assertIn("主食", category_stats)

        result = CostCalculator.simulate_ingredient_replace(
            dish1, "1", loaded_ings["4"], 200, "g", loaded_ings
        )
        self.assertIsNotNone(result)
        self.assertLess(result['cost_diff'], 0)

        loaded_ings["1"].update_price(70.0)
        analyses2 = CostCalculator.calculate_all_dishes(loaded_dishes, loaded_ings)
        self.assertGreater(analyses2[0].material_cost, analyses[0].material_cost)

    def test_price_history_chart(self):
        ing = self.ingredients["1"]
        base_time = datetime.now()

        ing.price_history = [
            PriceHistory(price=50.0, timestamp=base_time - timedelta(days=10)),
            PriceHistory(price=55.0, timestamp=base_time - timedelta(days=8)),
            PriceHistory(price=52.0, timestamp=base_time - timedelta(days=6)),
            PriceHistory(price=58.0, timestamp=base_time - timedelta(days=4)),
            PriceHistory(price=60.0, timestamp=base_time - timedelta(days=2)),
        ]

        data_points = [(ph.timestamp, ph.price) for ph in ing.price_history]
        chart = AsciiChart.draw_line_chart(data_points)

        self.assertIsInstance(chart, str)
        self.assertGreater(len(chart), 0)


def run_tests():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
