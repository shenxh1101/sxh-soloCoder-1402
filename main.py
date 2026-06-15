import sys
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from models import Ingredient, Dish, RecipeItem, DishCostAnalysis
from storage import DataStorage
from cost_calculator import CostCalculator, MarginAnalyzer
from csv_importer import CSVImporter
from ascii_chart import AsciiChart
from pdf_exporter import PDFExporter


def resolve_path(user_input: str, default_filename: str = "") -> str:
    if not user_input:
        user_input = default_filename
    if not os.path.isabs(user_input):
        user_input = os.path.join(os.getcwd(), user_input)
    dir_path = os.path.dirname(user_input)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    return user_input


def _display_dish_analysis_detail(analysis: DishCostAnalysis) -> None:
    dish = analysis.dish
    print()
    print(f"菜品名称: {dish.name}")
    print(f"菜品类别: {dish.category}")
    print(f"目标毛利率: {dish.target_margin * 100:.1f}%")
    print()
    print("-" * 70)
    print()
    print("配方明细:")
    print(f"{'原材料':<15} {'用量':<10} {'成本(元)':<12} {'占比':<10}")
    print("-" * 50)

    for name, cost in analysis.ingredient_costs:
        item = next((i for i in dish.recipe if i.ingredient_name == name), None)
        amount = item.amount if item else 0
        unit = item.unit if item else ''
        percentage = (cost / analysis.material_cost * 100) if analysis.material_cost > 0 else 0
        print(f"{name:<15} {amount:.0f}{unit:<7} {cost:<12.2f} {percentage:<10.1f}%")

    print("-" * 50)
    print()
    print(f"物料成本: ¥{analysis.material_cost:.2f}")
    print(f"建议售价: ¥{analysis.suggested_price:.2f}")
    print(f"毛利额:   ¥{analysis.gross_profit:.2f}")
    print(f"毛利率:   {analysis.gross_margin * 100:.1f}%")
    if analysis.total_calorie:
        print(f"总热量:   {analysis.total_calorie:.0f} kcal")
    print()


class RestaurantCostAnalyzer:
    def __init__(self):
        self.storage = DataStorage()
        self.ingredients: Dict[str, Ingredient] = {}
        self.dishes: List[Dish] = []
        self.analyses: List[DishCostAnalysis] = []
        self._load_data()

    def _load_data(self):
        self.ingredients = self.storage.load_ingredients()
        self.dishes = self.storage.load_dishes()
        if self.dishes and self.ingredients:
            self._recalculate_all()

    def _save_data(self):
        self.storage.save_ingredients(self.ingredients)
        self.storage.save_dishes(self.dishes)

    def _recalculate_all(self):
        try:
            self.analyses = CostCalculator.calculate_all_dishes(self.dishes, self.ingredients)
        except Exception as e:
            print(f"重新计算成本时出错: {e}")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str):
        self.clear_screen()
        width = 70
        print("=" * width)
        print(f"{title:^{width}}")
        print("=" * width)
        print()

    def print_menu(self):
        self.print_header("餐饮连锁店菜品成本卡与毛利率分析工具")
        print("【主菜单】")
        print()
        print("  1. 原材料管理")
        print("  2. 菜品管理")
        print("  3. 批量导入 (CSV)")
        print("  4. 一键重新计算所有菜品成本")
        print("  5. 毛利分析报告")
        print("  6. 菜品替换模拟")
        print("  7. 原材料价格走势")
        print("  8. 导出成本卡 (PDF)")
        print("  0. 退出程序")
        print()
        print("=" * 70)

    def ingredient_menu(self):
        while True:
            self.print_header("原材料管理")
            print(f"当前原材料数量: {len(self.ingredients)}")
            print()
            print("  1. 添加原材料")
            print("  2. 查看所有原材料")
            print("  3. 更新原材料价格")
            print("  4. 删除原材料")
            print("  0. 返回主菜单")
            print()

            choice = input("请选择操作: ").strip()

            if choice == '1':
                self.add_ingredient()
            elif choice == '2':
                self.list_ingredients()
            elif choice == '3':
                self.update_ingredient_price()
            elif choice == '4':
                self.delete_ingredient()
            elif choice == '0':
                break
            else:
                input("无效选择，按回车继续...")

    def add_ingredient(self):
        self.print_header("添加原材料")
        print("请输入原材料信息（留空返回）:")
        print()

        name = input("原材料名称: ").strip()
        if not name:
            return

        for ing in self.ingredients.values():
            if ing.name == name:
                print(f"错误: 原材料 '{name}' 已存在")
                input("按回车继续...")
                return

        print("单位选项: kg(千克), g(克), L(升), ml(毫升), 个, 把, 片")
        unit = input("采购单位: ").strip()
        if not unit:
            return

        valid_units = ['kg', 'g', 'L', 'ml', '个', '把', '片']
        if unit not in valid_units:
            print(f"错误: 无效的单位 '{unit}'，请使用 {valid_units}")
            input("按回车继续...")
            return

        try:
            price_str = input(f"采购单价 (元/{unit}): ").strip()
            if not price_str:
                return
            current_price = float(price_str)
            if current_price <= 0:
                raise ValueError("价格必须大于0")
        except ValueError as e:
            print(f"错误: {e}")
            input("按回车继续...")
            return

        calorie_str = input(f"每{unit}热量 (kcal，可选): ").strip()
        calorie_per_unit = float(calorie_str) if calorie_str else None

        ingredient = Ingredient(
            name=name,
            unit=unit,
            current_price=current_price,
            calorie_per_unit=calorie_per_unit
        )

        self.ingredients[ingredient.id] = ingredient
        self._save_data()

        print()
        print(f"✓ 成功添加原材料: {name} (ID: {ingredient.id})")
        input("按回车继续...")

    def list_ingredients(self):
        self.print_header("原材料列表")

        if not self.ingredients:
            print("暂无原材料数据")
            input("按回车继续...")
            return

        print(f"{'ID':<10} {'名称':<15} {'单位':<8} {'单价(元)':<12} {'热量(kcal)':<12} {'价格记录数':<10}")
        print("-" * 70)

        for ing in sorted(self.ingredients.values(), key=lambda x: x.name):
            calorie = f"{ing.calorie_per_unit:.0f}" if ing.calorie_per_unit else "-"
            print(f"{ing.id:<10} {ing.name:<15} {ing.unit:<8} {ing.current_price:<12.2f} {calorie:<12} {len(ing.price_history):<10}")

        print()
        input("按回车继续...")

    def update_ingredient_price(self):
        self.print_header("更新原材料价格")

        if not self.ingredients:
            print("暂无原材料数据")
            input("按回车继续...")
            return

        search_name = input("请输入要更新的原材料名称 (留空返回): ").strip()
        if not search_name:
            return

        ingredient = None
        for ing in self.ingredients.values():
            if ing.name == search_name:
                ingredient = ing
                break

        if not ingredient:
            print(f"未找到原材料: {search_name}")
            input("按回车继续...")
            return

        print()
        print(f"原材料: {ingredient.name}")
        print(f"当前单位: {ingredient.unit}")
        print(f"当前单价: {ingredient.current_price:.2f} 元/{ingredient.unit}")
        print()

        try:
            new_price_str = input(f"请输入新单价 (元/{ingredient.unit}, 留空返回): ").strip()
            if not new_price_str:
                return
            new_price = float(new_price_str)
            if new_price <= 0:
                raise ValueError("价格必须大于0")
        except ValueError as e:
            print(f"错误: {e}")
            input("按回车继续...")
            return

        ingredient.update_price(new_price)
        self._save_data()

        if self.dishes:
            self._recalculate_all()
            self._save_data()

        print()
        print(f"✓ 价格已更新: {ingredient.current_price:.2f} -> {new_price:.2f} 元/{ingredient.unit}")
        input("按回车继续...")

    def delete_ingredient(self):
        self.print_header("删除原材料")

        if not self.ingredients:
            print("暂无原材料数据")
            input("按回车继续...")
            return

        search_name = input("请输入要删除的原材料名称 (留空返回): ").strip()
        if not search_name:
            return

        ingredient = None
        ing_id = None
        for id, ing in self.ingredients.items():
            if ing.name == search_name:
                ingredient = ing
                ing_id = id
                break

        if not ingredient:
            print(f"未找到原材料: {search_name}")
            input("按回车继续...")
            return

        affected_dishes = []
        affected_dishes_detail = []
        for dish in self.dishes:
            for item in dish.recipe:
                if item.ingredient_id == ing_id:
                    affected_dishes.append(dish.name)
                    affected_dishes_detail.append((dish, item))
                    break

        dishes_to_delete = []
        dishes_to_modify = []

        if affected_dishes:
            print()
            print(f"⚠️  该原材料正在被 {len(affected_dishes)} 道菜品使用:")
            for dish, item in affected_dishes_detail:
                remaining_count = len(dish.recipe) - 1
                if remaining_count <= 0:
                    dishes_to_delete.append(dish)
                    print(f"  - {dish.name} ({dish.category}): 使用 {item.amount}{item.unit} → 删除后将无配方，【整道菜会被删除】")
                else:
                    dishes_to_modify.append(dish)
                    print(f"  - {dish.name} ({dish.category}): 使用 {item.amount}{item.unit} → 将从配方中移除该原料")

            print()
            confirm = input("确认删除原材料并自动处理关联菜品? (y/N): ").strip().lower()
            if confirm != 'y':
                print("已取消删除。")
                input("按回车继续...")
                return
        else:
            confirm = input(f"确认删除原材料 '{search_name}'? (y/N): ").strip().lower()
            if confirm != 'y':
                return

        if dishes_to_delete:
            for d in dishes_to_delete:
                if d in self.dishes:
                    self.dishes.remove(d)

        if dishes_to_modify:
            for dish in dishes_to_modify:
                dish.recipe = [item for item in dish.recipe if item.ingredient_id != ing_id]

        del self.ingredients[ing_id]
        self._save_data()

        if self.dishes:
            self._recalculate_all()
            self._save_data()

        print()
        print(f"✅ 已删除原材料: {search_name}")
        if dishes_to_delete:
            print(f"  - 已删除 {len(dishes_to_delete)} 道无剩余配方的菜品: {', '.join(d.name for d in dishes_to_delete)}")
        if dishes_to_modify:
            print(f"  - 已更新 {len(dishes_to_modify)} 道菜的配方: {', '.join(d.name for d in dishes_to_modify)}")
        if self.analyses:
            low_margin = MarginAnalyzer.get_low_margin_dishes(self.analyses, 0.4)
            print(f"  - 当前共 {len(self.analyses)} 道菜，低毛利菜品 {len(low_margin)} 道")
        print()
        input("按回车继续...")

    def dish_menu(self):
        while True:
            self.print_header("菜品管理")
            print(f"当前菜品数量: {len(self.dishes)}")
            print()
            print("  1. 添加菜品")
            print("  2. 查看所有菜品")
            print("  3. 查看菜品成本明细")
            print("  4. 删除菜品")
            print("  0. 返回主菜单")
            print()

            choice = input("请选择操作: ").strip()

            if choice == '1':
                self.add_dish()
            elif choice == '2':
                self.list_dishes()
            elif choice == '3':
                self.show_dish_detail()
            elif choice == '4':
                self.delete_dish()
            elif choice == '0':
                break
            else:
                input("无效选择，按回车继续...")

    def add_dish(self):
        self.print_header("添加菜品")

        if not self.ingredients:
            print("错误: 请先添加原材料")
            input("按回车继续...")
            return

        print("请输入菜品信息（留空返回）:")
        print()

        name = input("菜品名称: ").strip()
        if not name:
            return

        for dish in self.dishes:
            if dish.name == name:
                print(f"错误: 菜品 '{name}' 已存在")
                input("按回车继续...")
                return

        categories = ['凉菜', '热菜', '主食', '饮品']
        print("菜品类别选项:", ', '.join(categories))
        category = input("菜品类别: ").strip()
        if not category:
            return

        if category not in categories:
            print(f"错误: 无效的类别 '{category}'，请使用 {categories}")
            input("按回车继续...")
            return

        try:
            margin_str = input("目标毛利率 (0-1，默认0.6): ").strip()
            target_margin = float(margin_str) if margin_str else 0.6
            if target_margin <= 0 or target_margin >= 1:
                raise ValueError("毛利率必须在0到1之间")
        except ValueError as e:
            print(f"错误: {e}")
            input("按回车继续...")
            return

        print()
        print("可用原材料:")
        for i, ing in enumerate(sorted(self.ingredients.values(), key=lambda x: x.name), 1):
            calorie = f" ({ing.calorie_per_unit:.0f}kcal/{ing.unit})" if ing.calorie_per_unit else ""
            print(f"  {i}. {ing.name} - {ing.current_price:.2f}元/{ing.unit}{calorie}")

        print()
        print("请输入配方原材料（至少1种，输入 'done' 完成）:")

        recipe = []
        while len(recipe) < 100:
            print()
            ing_input = input(f"原材料 #{len(recipe) + 1} (名称或序号，输入 done 完成): ").strip()
            if not ing_input:
                continue
            if ing_input.lower() == 'done':
                break

            ingredient = None
            if ing_input.isdigit():
                idx = int(ing_input) - 1
                sorted_ings = sorted(self.ingredients.values(), key=lambda x: x.name)
                if 0 <= idx < len(sorted_ings):
                    ingredient = sorted_ings[idx]
            else:
                for ing in self.ingredients.values():
                    if ing.name == ing_input:
                        ingredient = ing
                        break

            if not ingredient:
                print(f"错误: 未找到原材料 '{ing_input}'")
                continue

            try:
                amount_str = input(f"  用量 ({ingredient.name}): ").strip()
                if not amount_str:
                    continue
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError("用量必须大于0")
            except ValueError as e:
                print(f"错误: {e}")
                continue

            print(f"  可用单位: g, ml, kg, L, 个, 把, 片")
            unit = input(f"  单位 ({ingredient.name}): ").strip()
            if not unit:
                continue

            valid_units = ['g', 'ml', 'kg', 'L', '个', '把', '片']
            if unit not in valid_units:
                print(f"错误: 无效的单位 '{unit}'")
                continue

            recipe_item = RecipeItem(
                ingredient_id=ingredient.id,
                ingredient_name=ingredient.name,
                amount=amount,
                unit=unit
            )
            recipe.append(recipe_item)
            print(f"  ✓ 已添加: {ingredient.name} {amount}{unit}")

        if len(recipe) < 1:
            print("错误: 至少需要1种原材料")
            input("按回车继续...")
            return

        dish = Dish(
            name=name,
            category=category,
            recipe=recipe,
            target_margin=target_margin
        )

        self.dishes.append(dish)
        self._recalculate_all()
        self._save_data()

        print()
        print(f"✓ 成功添加菜品: {name}")
        input("按回车继续...")

    def list_dishes(self):
        self.print_header("菜品列表")

        if not self.dishes:
            print("暂无菜品数据")
            input("按回车继续...")
            return

        if not self.analyses:
            self._recalculate_all()

        print(f"{'ID':<10} {'名称':<20} {'类别':<8} {'成本(元)':<10} {'建议售价(元)':<14} {'毛利率':<10}")
        print("-" * 70)

        for analysis in sorted(self.analyses, key=lambda x: x.dish.name):
            margin_color = "\033[91m" if analysis.gross_margin < 0.4 else ""
            reset_color = "\033[0m" if analysis.gross_margin < 0.4 else ""
            print(f"{analysis.dish.id:<10} {analysis.dish.name:<20} {analysis.dish.category:<8} "
                  f"{analysis.material_cost:<10.2f} {analysis.suggested_price:<14.2f} "
                  f"{margin_color}{analysis.gross_margin * 100:<10.1f}%{reset_color}")

        print()
        print("\033[91m红色\033[0m 表示毛利率低于40%")
        input("按回车继续...")

    def show_dish_detail(self):
        self.print_header("菜品成本明细")

        if not self.analyses:
            print("暂无菜品分析数据")
            input("按回车继续...")
            return

        search_name = input("请输入菜品名称 (留空返回): ").strip()
        if not search_name:
            return

        analysis = None
        for a in self.analyses:
            if a.dish.name == search_name:
                analysis = a
                break

        if not analysis:
            print(f"未找到菜品: {search_name}")
            input("按回车继续...")
            return

        _display_dish_analysis_detail(analysis)
        input("按回车继续...")

    def delete_dish(self):
        self.print_header("删除菜品")

        if not self.dishes:
            print("暂无菜品数据")
            input("按回车继续...")
            return

        search_name = input("请输入要删除的菜品名称 (留空返回): ").strip()
        if not search_name:
            return

        dish = None
        for d in self.dishes:
            if d.name == search_name:
                dish = d
                break

        if not dish:
            print(f"未找到菜品: {search_name}")
            input("按回车继续...")
            return

        confirm = input(f"确认删除菜品 '{search_name}'? (y/N): ").strip().lower()
        if confirm != 'y':
            return

        self.dishes.remove(dish)
        self._recalculate_all()
        self._save_data()

        print(f"✓ 已删除菜品: {search_name}")
        input("按回车继续...")

    def import_menu(self):
        while True:
            self.print_header("批量导入 (CSV)")
            print("  1. 导入原材料")
            print("  2. 导入菜品")
            print("  3. 生成原材料导入模板")
            print("  4. 生成菜品导入模板")
            print("  0. 返回主菜单")
            print()

            choice = input("请选择操作: ").strip()

            if choice == '1':
                self.import_ingredients_csv()
            elif choice == '2':
                self.import_dishes_csv()
            elif choice == '3':
                path = input("请输入模板保存路径 (默认: ingredients_template.csv): ").strip()
                resolved = resolve_path(path, "ingredients_template.csv")
                CSVImporter.generate_ingredient_template(resolved)
                print(f"✅ 模板已生成: {resolved}")
                input("按回车继续...")
            elif choice == '4':
                path = input("请输入模板保存路径 (默认: dishes_template.csv): ").strip()
                resolved = resolve_path(path, "dishes_template.csv")
                CSVImporter.generate_dish_template(resolved)
                print(f"✅ 模板已生成: {resolved}")
                input("按回车继续...")
            elif choice == '0':
                break
            else:
                input("无效选择，按回车继续...")

    def import_ingredients_csv(self):
        self.print_header("导入原材料")

        file_path = input("请输入CSV文件路径 (留空返回): ").strip()
        if not file_path:
            return

        ingredients, errors = CSVImporter.import_ingredients(file_path)

        if errors:
            print()
            print("错误信息:")
            for error in errors:
                print(f"  - {error}")
            print()

        if not ingredients:
            print("未导入任何原材料")
            input("按回车继续...")
            return

        added = 0
        updated = 0
        for ing in ingredients:
            existing = None
            for existing_ing in self.ingredients.values():
                if existing_ing.name == ing.name:
                    existing = existing_ing
                    break

            if existing:
                existing.update_price(ing.current_price)
                if ing.calorie_per_unit:
                    existing.calorie_per_unit = ing.calorie_per_unit
                updated += 1
            else:
                self.ingredients[ing.id] = ing
                added += 1

        self._save_data()
        if self.dishes:
            self._recalculate_all()
            self._save_data()

        print()
        print(f"✓ 导入完成: 新增 {added} 种，更新 {updated} 种")
        input("按回车继续...")

    def import_dishes_csv(self):
        self.print_header("导入菜品")

        if not self.ingredients:
            print("错误: 请先导入原材料")
            input("按回车继续...")
            return

        file_path = input("请输入CSV文件路径 (留空返回): ").strip()
        if not file_path:
            return

        dishes, errors = CSVImporter.import_dishes(file_path, self.ingredients)

        if errors:
            print()
            print("错误信息:")
            for error in errors:
                print(f"  - {error}")
            print()

        if not dishes:
            print("未导入任何菜品")
            input("按回车继续...")
            return

        added = 0
        updated = 0
        for dish in dishes:
            existing = None
            for existing_dish in self.dishes:
                if existing_dish.name == dish.name:
                    existing = existing_dish
                    break

            if existing:
                existing.recipe = dish.recipe
                existing.target_margin = dish.target_margin
                existing.category = dish.category
                updated += 1
            else:
                self.dishes.append(dish)
                added += 1

        self._recalculate_all()
        self._save_data()

        print()
        print(f"✓ 导入完成: 新增 {added} 道，更新 {updated} 道")
        input("按回车继续...")

    def recalculate_all(self):
        self.print_header("一键重新计算所有菜品成本")

        if not self.dishes:
            print("暂无菜品数据")
            input("按回车继续...")
            return

        if not self.ingredients:
            print("暂无原材料数据")
            input("按回车继续...")
            return

        try:
            self._recalculate_all()
            self._save_data()

            print(f"✓ 已重新计算 {len(self.analyses)} 道菜品的成本")
            print()

            low_margin = MarginAnalyzer.get_low_margin_dishes(self.analyses, 0.4)
            if low_margin:
                print(f"警告: 有 {len(low_margin)} 道菜品毛利率低于40%:")
                for a in low_margin:
                    print(f"  - {a.dish.name}: {a.gross_margin * 100:.1f}%")

        except Exception as e:
            print(f"计算失败: {e}")

        print()
        input("按回车继续...")

    def generate_margin_report(self):
        self.print_header("毛利分析报告")

        if not self.analyses:
            print("暂无菜品分析数据")
            input("按回车继续...")
            return

        category_stats = MarginAnalyzer.analyze_by_category(self.analyses)
        low_margin_dishes = MarginAnalyzer.get_low_margin_dishes(self.analyses, 0.4)

        print("【按类别统计平均毛利率】")
        print()
        category_data = []
        for category, stats in sorted(category_stats.items()):
            category_data.append((category, stats['avg_margin'] * 100))
            print(f"  {category:<8} 平均毛利率: {stats['avg_margin'] * 100:.1f}% (共{stats['count']}道菜)")

        print()
        print(AsciiChart.draw_bar_chart(category_data, "各类别平均毛利率对比", 30))
        print()

        print("=" * 70)
        print()
        print("【所有菜品成本分析】")
        print()
        print(f"{'名称':<20} {'类别':<8} {'成本(元)':<10} {'售价(元)':<12} {'毛利额(元)':<12} {'毛利率':<10}")
        print("-" * 70)

        for analysis in sorted(self.analyses, key=lambda x: x.gross_margin, reverse=True):
            margin = analysis.gross_margin * 100
            margin_str = f"{margin:.1f}%"
            if analysis.gross_margin < 0.4:
                margin_str = f"\033[91m{margin_str} ⚠\033[0m"
            print(f"{analysis.dish.name:<20} {analysis.dish.category:<8} "
                  f"{analysis.material_cost:<10.2f} {analysis.suggested_price:<12.2f} "
                  f"{analysis.gross_profit:<12.2f} {margin_str}")

        print()
        print("=" * 70)
        print()

        if low_margin_dishes:
            print(f"\033[91m⚠ 警告: 有 {len(low_margin_dishes)} 道菜品毛利率低于40%\033[0m")
            print()
            for a in low_margin_dishes:
                print(f"  - {a.dish.name} ({a.dish.category}): 毛利率 {a.gross_margin * 100:.1f}%")
        else:
            print("✓ 所有菜品毛利率均高于40%")

        print()
        input("按回车继续...")

    def ingredient_replace_simulation(self):
        self.print_header("菜品替换模拟")

        if not self.analyses:
            print("暂无菜品分析数据")
            input("按回车继续...")
            return

        dish_name = input("请输入要模拟的菜品名称 (留空返回): ").strip()
        if not dish_name:
            return

        dish = None
        original_analysis = None
        for idx, d in enumerate(self.dishes):
            if d.name == dish_name:
                dish = d
                original_analysis = self.analyses[idx]
                break

        if not dish:
            print(f"未找到菜品: {dish_name}")
            input("按回车继续...")
            return

        print()
        print("菜品配方:")
        recipe_items = list(dish.recipe)
        for i, item in enumerate(recipe_items, 1):
            ingredient = self.ingredients.get(item.ingredient_id)
            price = ingredient.current_price if ingredient else 0
            unit = ingredient.unit if ingredient else ''
            print(f"  [{i}] {item.ingredient_name}: {item.amount}{item.unit} (单价: {price}元/{unit})")

        print()
        try:
            choice_str = input("请选择要替换的原材料序号 (如1, 留空返回): ").strip()
            if not choice_str:
                return
            choice_idx = int(choice_str)
            if choice_idx < 1 or choice_idx > len(recipe_items):
                raise ValueError(f"序号需在 1~{len(recipe_items)} 之间")
            recipe_pos = choice_idx - 1
        except ValueError as e:
            print(f"无效的选择: {e}")
            input("按回车继续...")
            return

        original_item = recipe_items[recipe_pos]
        original_ingredient = self.ingredients.get(original_item.ingredient_id)

        print()
        print(f"▶ 已选择 #{choice_idx}: {original_item.ingredient_name} {original_item.amount}{original_item.unit}")
        if original_ingredient and original_ingredient.calorie_per_unit:
            print(f"  每{original_ingredient.unit}热量: {original_ingredient.calorie_per_unit:.0f} kcal")

        print()
        all_ings = sorted(self.ingredients.values(), key=lambda x: x.name)
        available_list = [ing for ing in all_ings if ing.id != original_item.ingredient_id]

        print("可用替换原材料:")
        for i, ing in enumerate(available_list, 1):
            calorie = f" ({ing.calorie_per_unit:.0f}kcal/{ing.unit})" if ing.calorie_per_unit else ""
            print(f"  [{i}] {ing.name} - {ing.current_price:.2f}元/{ing.unit}{calorie}")

        print()
        try:
            replace_choice_str = input("请选择替换的原材料序号 (留空返回): ").strip()
            if not replace_choice_str:
                return
            replace_idx = int(replace_choice_str)
            if replace_idx < 1 or replace_idx > len(available_list):
                raise ValueError(f"序号需在 1~{len(available_list)} 之间")
            replace_pos = replace_idx - 1
        except ValueError as e:
            print(f"无效的选择: {e}")
            input("按回车继续...")
            return

        replace_ingredient = available_list[replace_pos]
        print(f"▶ 已选择替换为 #{replace_idx}: {replace_ingredient.name} ({replace_ingredient.current_price:.2f}元/{replace_ingredient.unit})")

        try:
            default_amount = original_item.amount
            amount_str = input(f"请输入替换用量 [{default_amount}{original_item.unit}]: ").strip()
            if not amount_str:
                replace_amount = default_amount
            else:
                replace_amount = float(amount_str)
                if replace_amount <= 0:
                    raise ValueError
        except ValueError:
            print("无效的用量")
            input("按回车继续...")
            return

        default_unit = original_item.unit
        unit_input = input(f"请输入替换单位 [{default_unit}]: ").strip()
        replace_unit = unit_input if unit_input else default_unit

        try:
            result = CostCalculator.simulate_ingredient_replace(
                dish,
                original_item.ingredient_id,
                replace_ingredient,
                replace_amount,
                replace_unit,
                self.ingredients
            )
        except Exception as e:
            print(f"模拟失败: {e}")
            input("按回车继续...")
            return

        ori_analysis = result['original']
        new_analysis = result['new']
        cost_change = result['cost_diff']
        cost_sign = "+" if cost_change > 0 else ""
        price_change = result['price_diff']
        price_sign = "+" if price_change > 0 else ""

        self.print_header("替换模拟结果对比")
        print(f"菜品: {dish.name}")
        print(f"替换: {original_item.ingredient_name} → {replace_ingredient.name}")
        print()
        print("=" * 70)
        print(f"{'项目':<16} {'替换前':<18} {'替换后':<18} {'变化':<16}")
        print("-" * 70)

        print(f"{'原材料':<16} {original_item.ingredient_name:<18} {replace_ingredient.name:<18} {'':<16}")
        print(f"{'用量':<16} {f'{original_item.amount}{original_item.unit}':<18} {f'{replace_amount}{replace_unit}':<18} {'':<16}")
        profit_change = new_analysis.gross_profit - ori_analysis.gross_profit
        profit_sign = "+" if profit_change > 0 else ""
        print(f"{'物料成本(元)':<16} {ori_analysis.material_cost:<18.2f} {new_analysis.material_cost:<18.2f} {f'{cost_sign}{cost_change:.2f}':<16}")
        print(f"{'建议售价(元)':<16} {ori_analysis.suggested_price:<18.2f} {new_analysis.suggested_price:<18.2f} {f'{price_sign}{price_change:.2f}':<16}")
        print(f"{'毛利额(元)':<16} {ori_analysis.gross_profit:<18.2f} {new_analysis.gross_profit:<18.2f} {f'{profit_sign}{profit_change:.2f}':<16}")
        print(f"{'毛利率':<16} {f'{ori_analysis.gross_margin*100:.1f}%':<18} {f'{new_analysis.gross_margin*100:.1f}%':<18} {f'{(new_analysis.gross_margin-ori_analysis.gross_margin)*100:+.1f}%':<16}")

        if result['calorie_diff'] is not None:
            calorie_change = result['calorie_diff']
            calorie_sign = "+" if calorie_change > 0 else ""
            print(f"{'总热量(kcal)':<16} {f'{ori_analysis.total_calorie:.0f}':<18} {f'{new_analysis.total_calorie:.0f}':<18} {f'{calorie_sign}{calorie_change:.0f}':<16}")

        print("=" * 70)
        print()
        if cost_change < 0:
            print(f"✅ 成本降低: {-cost_change:.2f} 元 (降幅 {-cost_change/ori_analysis.material_cost*100:.1f}%)")
        elif cost_change > 0:
            print(f"⚠️  成本增加: {cost_change:.2f} 元 (增幅 {cost_change/ori_analysis.material_cost*100:.1f}%)")
        else:
            print("➖ 成本无变化")

        print()
        print("--- 替换后配方明细 ---")
        new_ingredient_costs_map = {name: cost for name, cost in new_analysis.ingredient_costs}
        print(f"{'原材料':<15} {'用量':<10} {'成本(元)':<12} {'占比':<10}")
        print("-" * 50)
        for item in new_analysis.dish.recipe:
            cost = new_ingredient_costs_map.get(item.ingredient_name, 0.0)
            percentage = (cost / new_analysis.material_cost * 100) if new_analysis.material_cost > 0 else 0
            marker = " ← 替换项" if item.ingredient_id == replace_ingredient.id else ""
            print(f"{item.ingredient_name:<15} {item.amount:.0f}{item.unit:<7} {cost:<12.2f} {percentage:<10.1f}%{marker}")
        print()

        apply = input("是否应用此替换到菜品配方? (y/N): ").strip().lower()
        if apply == 'y':
            for item in dish.recipe:
                if item.ingredient_id == original_item.ingredient_id:
                    item.ingredient_id = replace_ingredient.id
                    item.ingredient_name = replace_ingredient.name
                    item.amount = replace_amount
                    item.unit = replace_unit
                    break

            if replace_ingredient.id not in self.ingredients:
                self.ingredients[replace_ingredient.id] = replace_ingredient

            self._recalculate_all()
            self._save_data()
            print()
            print("✅ 已应用替换！以下是该菜品最新成本明细：")
            print()
            updated_analysis = None
            for a in self.analyses:
                if a.dish.id == dish.id:
                    updated_analysis = a
                    break
            if updated_analysis:
                _display_dish_analysis_detail(updated_analysis)
        else:
            print()
            print("未应用替换。")

        print()
        input("按回车继续...")

    def show_price_history(self):
        self.print_header("原材料价格走势")

        if not self.ingredients:
            print("暂无原材料数据")
            input("按回车继续...")
            return

        search_name = input("请输入原材料名称 (留空返回): ").strip()
        if not search_name:
            return

        ingredient = None
        for ing in self.ingredients.values():
            if ing.name == search_name:
                ingredient = ing
                break

        if not ingredient:
            print(f"未找到原材料: {search_name}")
            input("按回车继续...")
            return

        if len(ingredient.price_history) < 2:
            print()
            print(f"原材料: {ingredient.name}")
            print(f"当前价格: {ingredient.current_price:.2f} 元/{ingredient.unit}")
            print()
            print("价格记录不足，无法生成走势图 (至少需要2条记录)")
            input("按回车继续...")
            return

        print()
        print(f"原材料: {ingredient.name}")
        print(f"当前价格: {ingredient.current_price:.2f} 元/{ingredient.unit}")
        print(f"价格记录数: {len(ingredient.price_history)}")
        print()

        data_points = [(ph.timestamp, ph.price) for ph in ingredient.price_history]
        print(AsciiChart.draw_line_chart(
            data_points,
            title=f"{ingredient.name} 价格走势 (元/{ingredient.unit})",
            height=12,
            width=70
        ))

        print()
        print("历史价格记录:")
        print(f"{'日期':<20} {'价格(元)':<12} {'变动':<15}")
        print("-" * 50)

        prev_price = None
        for ph in sorted(ingredient.price_history, key=lambda x: x.timestamp):
            date_str = ph.timestamp.strftime('%Y-%m-%d %H:%M')
            change = ""
            if prev_price is not None:
                diff = ph.price - prev_price
                sign = "+" if diff > 0 else ""
                change = f"{sign}{diff:.2f}"
            print(f"{date_str:<20} {ph.price:<12.2f} {change:<15}")
            prev_price = ph.price

        print()
        input("按回车继续...")

    def export_pdf(self):
        self.print_header("导出成本卡 (PDF)")

        if not self.analyses:
            print("暂无菜品分析数据")
            input("按回车继续...")
            return

        if not PDFExporter.is_available():
            print("错误: 未安装reportlab库，无法导出PDF")
            print("请运行: pip install reportlab")
            input("按回车继续...")
            return

        print("导出选项:")
        print("  1. 导出所有菜品")
        print("  2. 按类别导出")
        print("  3. 导出单个菜品")
        print("  0. 返回")
        print()

        choice = input("请选择: ").strip()

        analyses_to_export = []
        if choice == '1':
            analyses_to_export = self.analyses
        elif choice == '2':
            categories = list(set([a.dish.category for a in self.analyses]))
            print()
            print("可用类别:", ', '.join(categories))
            cat = input("请输入要导出的类别: ").strip()
            analyses_to_export = [a for a in self.analyses if a.dish.category == cat]
            if not analyses_to_export:
                print(f"未找到类别为 '{cat}' 的菜品")
                input("按回车继续...")
                return
        elif choice == '3':
            name = input("请输入菜品名称: ").strip()
            for a in self.analyses:
                if a.dish.name == name:
                    analyses_to_export = [a]
                    break
            if not analyses_to_export:
                print(f"未找到菜品: {name}")
                input("按回车继续...")
                return
        elif choice == '0':
            return
        else:
            print("无效选择")
            input("按回车继续...")
            return

        default_filename = f"成本卡_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_input = input(f"请输入输出文件名或路径 (默认: {default_filename}): ").strip()
        output_path = resolve_path(output_input, default_filename)

        title = input("请输入报告标题 (默认: 餐饮连锁店菜品成本卡): ").strip()
        if not title:
            title = "餐饮连锁店菜品成本卡"

        print(f"正在导出到: {output_path} ...")
        success = PDFExporter.export_cost_cards(analyses_to_export, output_path, title)

        if success:
            print()
            print(f"✓ 成功导出 {len(analyses_to_export)} 道菜的成本卡")

        input("按回车继续...")

    def run(self):
        while True:
            self.print_menu()
            choice = input("请选择操作: ").strip()

            if choice == '1':
                self.ingredient_menu()
            elif choice == '2':
                self.dish_menu()
            elif choice == '3':
                self.import_menu()
            elif choice == '4':
                self.recalculate_all()
            elif choice == '5':
                self.generate_margin_report()
            elif choice == '6':
                self.ingredient_replace_simulation()
            elif choice == '7':
                self.show_price_history()
            elif choice == '8':
                self.export_pdf()
            elif choice == '0':
                self.clear_screen()
                print("感谢使用！再见！")
                sys.exit(0)
            else:
                input("无效选择，按回车继续...")


def main():
    try:
        app = RestaurantCostAnalyzer()
        app.run()
    except KeyboardInterrupt:
        print("\n\n程序已退出")
    except Exception as e:
        print(f"\n程序发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
