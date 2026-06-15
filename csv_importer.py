import csv
import os
from typing import List, Dict, Tuple, Optional
from models import Ingredient, Dish, RecipeItem


class CSVImporter:
    @staticmethod
    def import_ingredients(file_path: str) -> Tuple[List[Ingredient], List[str]]:
        ingredients = []
        errors = []

        if not os.path.exists(file_path):
            errors.append(f"文件不存在: {file_path}")
            return ingredients, errors

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                required_fields = ['name', 'unit', 'current_price']

                for row_num, row in enumerate(reader, start=2):
                    missing_fields = [field for field in required_fields if field not in row or not row[field].strip()]
                    if missing_fields:
                        errors.append(f"第{row_num}行: 缺少必填字段 {', '.join(missing_fields)}")
                        continue

                    try:
                        name = row['name'].strip()
                        unit = row['unit'].strip()
                        current_price = float(row['current_price'].strip())
                        calorie_per_unit = float(row['calorie_per_unit'].strip()) if row.get('calorie_per_unit', '').strip() else None

                        ingredient = Ingredient(
                            name=name,
                            unit=unit,
                            current_price=current_price,
                            calorie_per_unit=calorie_per_unit
                        )
                        ingredients.append(ingredient)
                    except ValueError as e:
                        errors.append(f"第{row_num}行: 数据格式错误 - {e}")
                    except Exception as e:
                        errors.append(f"第{row_num}行: 未知错误 - {e}")

        except Exception as e:
            errors.append(f"读取CSV文件失败: {e}")

        return ingredients, errors

    @staticmethod
    def import_dishes(
        file_path: str,
        existing_ingredients: Dict[str, Ingredient]
    ) -> Tuple[List[Dish], List[str]]:
        dishes = []
        errors = []

        if not os.path.exists(file_path):
            errors.append(f"文件不存在: {file_path}")
            return dishes, errors

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                required_fields = ['name', 'category', 'ingredients']

                dish_data: Dict[str, Dict] = {}

                for row_num, row in enumerate(reader, start=2):
                    missing_fields = [field for field in required_fields if field not in row or not row[field].strip()]
                    if missing_fields:
                        errors.append(f"第{row_num}行: 缺少必填字段 {', '.join(missing_fields)}")
                        continue

                    try:
                        dish_name = row['name'].strip()
                        category = row['category'].strip()
                        target_margin = float(row['target_margin'].strip()) if row.get('target_margin', '').strip() else 0.6
                        ingredient_name = row['ingredients'].strip()
                        amount = float(row['amount'].strip()) if row.get('amount', '').strip() else 0
                        unit = row['unit'].strip() if row.get('unit', '').strip() else ''

                        if dish_name not in dish_data:
                            dish_data[dish_name] = {
                                'category': category,
                                'target_margin': target_margin,
                                'recipe': []
                            }

                        if ingredient_name and amount > 0 and unit:
                            ingredient = None
                            for ing in existing_ingredients.values():
                                if ing.name == ingredient_name:
                                    ingredient = ing
                                    break

                            if ingredient is None:
                                errors.append(f"第{row_num}行: 未找到原材料 '{ingredient_name}'，请先导入原材料")
                                continue

                            recipe_item = RecipeItem(
                                ingredient_id=ingredient.id,
                                ingredient_name=ingredient.name,
                                amount=amount,
                                unit=unit
                            )
                            dish_data[dish_name]['recipe'].append(recipe_item)

                    except ValueError as e:
                        errors.append(f"第{row_num}行: 数据格式错误 - {e}")
                    except Exception as e:
                        errors.append(f"第{row_num}行: 未知错误 - {e}")

                for dish_name, data in dish_data.items():
                    if len(data['recipe']) < 1:
                        errors.append(f"菜品 '{dish_name}': 至少需要1种原材料")
                        continue

                    dish = Dish(
                        name=dish_name,
                        category=data['category'],
                        recipe=data['recipe'],
                        target_margin=data['target_margin']
                    )
                    dishes.append(dish)

        except Exception as e:
            errors.append(f"读取CSV文件失败: {e}")

        return dishes, errors

    @staticmethod
    def generate_ingredient_template(output_path: str) -> None:
        dir_part = os.path.dirname(output_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'unit', 'current_price', 'calorie_per_unit'])
            writer.writerow(['牛肉', 'kg', '60.0', '2500'])
            writer.writerow(['洋葱', 'kg', '5.0', '400'])
            writer.writerow(['酱油', 'L', '12.0', '200'])
            writer.writerow(['鸡肉', 'kg', '25.0', '1650'])

    @staticmethod
    def generate_dish_template(output_path: str) -> None:
        dir_part = os.path.dirname(output_path)
        if dir_part:
            os.makedirs(dir_part, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'category', 'target_margin', 'ingredients', 'amount', 'unit'])
            writer.writerow(['洋葱炒牛肉', '热菜', '0.6', '牛肉', '200', 'g'])
            writer.writerow(['洋葱炒牛肉', '热菜', '0.6', '洋葱', '50', 'g'])
            writer.writerow(['洋葱炒牛肉', '热菜', '0.6', '酱油', '10', 'ml'])
