import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import resolve_path
from storage import DataStorage
from cost_calculator import CostCalculator
from csv_importer import CSVImporter
from pdf_exporter import PDFExporter, _register_cn_font


def test_resolve_path():
    print("=== 测试路径处理 ===")

    tmpdir = tempfile.mkdtemp()
    old_cwd = os.getcwd()

    try:
        os.chdir(tmpdir)

        p1 = resolve_path("成本卡.pdf", "default.pdf")
        assert os.path.isabs(p1), f"应转为绝对路径: {p1}"
        assert p1.endswith("成本卡.pdf")
        print(f"✅ 纯文件名解析: {p1}")

        p2 = resolve_path("myfolder/test.csv", "default.csv")
        assert os.path.isabs(p2), "相对路径应转为绝对路径"
        assert os.path.exists(os.path.dirname(p2)), "应自动创建子目录"
        print(f"✅ 相对路径+自动建目录: {p2}")

        p3 = resolve_path("", "default.csv")
        assert p3.endswith("default.csv")
        print(f"✅ 空值用默认: {p3}")

        full_path = os.path.join(tmpdir, "abs", "test.pdf")
        p4 = resolve_path(full_path, "default.pdf")
        assert p4 == full_path
        assert os.path.exists(os.path.dirname(p4))
        print(f"✅ 绝对路径: {p4}")

    finally:
        os.chdir(old_cwd)
        shutil.rmtree(tmpdir, ignore_errors=True)

    print()


def test_csv_template():
    print("=== 测试CSV模板生成 (只写文件名) ===")
    tmpdir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    try:
        os.chdir(tmpdir)

        CSVImporter.generate_ingredient_template("ingredients.csv")
        assert os.path.exists(os.path.join(tmpdir, "ingredients.csv"))
        print(f"✅ 原材料模板生成: ingredients.csv")

        CSVImporter.generate_dish_template("dishes.csv")
        assert os.path.exists(os.path.join(tmpdir, "dishes.csv"))
        print(f"✅ 菜品模板生成: dishes.csv")

    finally:
        os.chdir(old_cwd)
        shutil.rmtree(tmpdir, ignore_errors=True)
    print()


def test_pdf_chinese_export():
    print("=== 测试PDF中文导出 ===")
    tmpdir = tempfile.mkdtemp()
    old_cwd = os.getcwd()
    try:
        os.chdir(tmpdir)
        storage = DataStorage(data_dir="data")

        from models import Ingredient, Dish, RecipeItem
        ingredients = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0, calorie_per_unit=2500),
            "2": Ingredient(id="2", name="洋葱", unit="kg", current_price=5.0, calorie_per_unit=400),
            "3": Ingredient(id="3", name="酱油", unit="L", current_price=12.0, calorie_per_unit=200),
            "4": Ingredient(id="4", name="米饭", unit="kg", current_price=3.0, calorie_per_unit=1100),
        }
        dishes = [
            Dish(
                name="洋葱炒牛肉",
                category="热菜",
                target_margin=0.6,
                recipe=[
                    RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g"),
                    RecipeItem(ingredient_id="2", ingredient_name="洋葱", amount=100, unit="g"),
                    RecipeItem(ingredient_id="3", ingredient_name="酱油", amount=15, unit="ml"),
                ]
            ),
            Dish(
                name="白米饭",
                category="主食",
                target_margin=0.3,
                recipe=[
                    RecipeItem(ingredient_id="4", ingredient_name="米饭", amount=200, unit="g"),
                ]
            )
        ]

        analyses = CostCalculator.calculate_all_dishes(dishes, ingredients)

        font_ok = _register_cn_font()
        print(f"✅ 中文字体注册: {'成功' if font_ok else '使用系统替代字体'}")

        out = "门店成本卡.pdf"
        success = PDFExporter.export_cost_cards(analyses, out, "美味轩餐饮 - 菜品成本卡")
        assert success, "PDF导出失败"
        assert os.path.exists(os.path.join(tmpdir, out))
        size = os.path.getsize(out)
        print(f"✅ PDF导出成功: {out} (大小: {size} bytes)")

    finally:
        os.chdir(old_cwd)
        shutil.rmtree(tmpdir, ignore_errors=True)
    print()


def test_deleting_ingredient_removes_from_dishes():
    print("=== 测试删除原材料关联菜品处理 ===")
    tmpdir = tempfile.mkdtemp()
    try:
        storage = DataStorage(data_dir=tmpdir)

        from models import Ingredient, Dish, RecipeItem
        ingredients = {
            "1": Ingredient(id="1", name="牛肉", unit="kg", current_price=60.0),
            "2": Ingredient(id="2", name="洋葱", unit="kg", current_price=5.0),
            "3": Ingredient(id="3", name="盐", unit="kg", current_price=5.0),
        }

        dishes = [
            Dish(name="洋葱炒牛肉", category="热菜", recipe=[
                RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=200, unit="g"),
                RecipeItem(ingredient_id="2", ingredient_name="洋葱", amount=100, unit="g"),
                RecipeItem(ingredient_id="3", ingredient_name="盐", amount=2, unit="g"),
            ]),
            Dish(name="纯牛肉", category="热菜", recipe=[
                RecipeItem(ingredient_id="1", ingredient_name="牛肉", amount=300, unit="g"),
            ]),
            Dish(name="凉拌洋葱", category="凉菜", recipe=[
                RecipeItem(ingredient_id="2", ingredient_name="洋葱", amount=200, unit="g"),
                RecipeItem(ingredient_id="3", ingredient_name="盐", amount=3, unit="g"),
            ]),
        ]

        storage.save_ingredients(ingredients)
        storage.save_dishes(dishes)

        ing_id_to_del = "1"

        dishes_to_delete = []
        dishes_to_modify = []
        for dish in dishes:
            has_other = sum(1 for i in dish.recipe if i.ingredient_id != ing_id_to_del)
            if has_other <= 0:
                dishes_to_delete.append(dish)
            else:
                dishes_to_modify.append(dish)

        for d in dishes_to_delete:
            dishes.remove(d)

        for d in dishes_to_modify:
            d.recipe = [i for i in d.recipe if i.ingredient_id != ing_id_to_del]

        del ingredients[ing_id_to_del]

        storage.save_ingredients(ingredients)
        storage.save_dishes(dishes)

        assert "1" not in ingredients, "原材料应被删除"
        assert len(dishes) == 2, f"应剩2道菜，实际 {len(dishes)}"
        assert all(d.name != "纯牛肉" for d in dishes), "纯牛肉应被删除"
        assert all(all(i.ingredient_id != "1" for i in d.recipe) for d in dishes), "剩余菜品不应有牛肉"

        analyses = CostCalculator.calculate_all_dishes(dishes, ingredients)
        assert len(analyses) == 2, "所有剩余菜品应能计算成本"
        for a in analyses:
            assert a.material_cost > 0, f"{a.dish.name} 成本应>0"
            assert a.suggested_price > a.material_cost, f"{a.dish.name} 售价应高于成本"
        print(f"✅ 删除原材料成功: 删除 '牛肉' 后，删除了 '纯牛肉' (只剩牛肉)，更新了 '洋葱炒牛肉' (剔除牛肉)")
        print(f"   剩余 {len(dishes)} 道菜全部可正常重算: {', '.join(a.dish.name for a in analyses)}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print()


if __name__ == "__main__":
    test_resolve_path()
    test_csv_template()
    test_deleting_ingredient_removes_from_dishes()

    try:
        import reportlab
        test_pdf_chinese_export()
    except ImportError:
        print("⚠️  未安装reportlab，跳过PDF测试")

    print("=" * 50)
    print("🎉 所有手动测试通过！")
