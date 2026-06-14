from typing import List, Dict, Optional
from models import Ingredient, Dish, DishCostAnalysis, RecipeItem


class CostCalculator:
    @staticmethod
    def calculate_dish_cost(dish: Dish, ingredients: Dict[str, Ingredient]) -> DishCostAnalysis:
        material_cost = 0.0
        total_calorie: Optional[float] = 0.0
        ingredient_costs = []
        has_calorie_data = True

        for recipe_item in dish.recipe:
            ingredient = ingredients.get(recipe_item.ingredient_id)
            if ingredient is None:
                raise ValueError(f"未找到原材料: {recipe_item.ingredient_name} (ID: {recipe_item.ingredient_id})")

            item_cost = ingredient.calculate_cost(recipe_item.amount, recipe_item.unit)
            material_cost += item_cost
            ingredient_costs.append((recipe_item.ingredient_name, item_cost))

            item_calorie = ingredient.calculate_calorie(recipe_item.amount, recipe_item.unit)
            if item_calorie is None:
                has_calorie_data = False
            elif total_calorie is not None:
                total_calorie += item_calorie

        if not has_calorie_data:
            total_calorie = None

        if dish.target_margin >= 1:
            raise ValueError("目标毛利率必须小于1")

        suggested_price = material_cost / (1 - dish.target_margin)
        gross_profit = suggested_price - material_cost
        gross_margin = gross_profit / suggested_price if suggested_price > 0 else 0

        return DishCostAnalysis(
            dish=dish,
            material_cost=material_cost,
            suggested_price=suggested_price,
            gross_profit=gross_profit,
            gross_margin=gross_margin,
            total_calorie=total_calorie,
            ingredient_costs=ingredient_costs
        )

    @staticmethod
    def calculate_all_dishes(dishes: List[Dish], ingredients: Dict[str, Ingredient]) -> List[DishCostAnalysis]:
        analyses = []
        for dish in dishes:
            analysis = CostCalculator.calculate_dish_cost(dish, ingredients)
            analyses.append(analysis)
        return analyses

    @staticmethod
    def simulate_ingredient_replace(
        dish: Dish,
        original_ingredient_id: str,
        replace_ingredient: Ingredient,
        replace_amount: float,
        replace_unit: str,
        ingredients: Dict[str, Ingredient]
    ) -> Dict:
        original_analysis = CostCalculator.calculate_dish_cost(dish, ingredients)

        new_recipe = []
        for item in dish.recipe:
            if item.ingredient_id == original_ingredient_id:
                new_recipe.append(RecipeItem(
                    ingredient_id=replace_ingredient.id,
                    ingredient_name=replace_ingredient.name,
                    amount=replace_amount,
                    unit=replace_unit
                ))
            else:
                new_recipe.append(item)

        new_dish = Dish(
            name=dish.name,
            category=dish.category,
            recipe=new_recipe,
            target_margin=dish.target_margin,
            id=dish.id
        )

        new_ingredients = dict(ingredients)
        new_ingredients[replace_ingredient.id] = replace_ingredient

        new_analysis = CostCalculator.calculate_dish_cost(new_dish, new_ingredients)

        original_ingredient = ingredients.get(original_ingredient_id)
        original_item = next((item for item in dish.recipe if item.ingredient_id == original_ingredient_id), None)

        return {
            'original': original_analysis,
            'new': new_analysis,
            'original_ingredient': original_ingredient,
            'replace_ingredient': replace_ingredient,
            'original_amount': original_item.amount if original_item else 0,
            'original_unit': original_item.unit if original_item else '',
            'replace_amount': replace_amount,
            'replace_unit': replace_unit,
            'cost_diff': new_analysis.material_cost - original_analysis.material_cost,
            'price_diff': new_analysis.suggested_price - original_analysis.suggested_price,
            'calorie_diff': (new_analysis.total_calorie or 0) - (original_analysis.total_calorie or 0) if (new_analysis.total_calorie is not None and original_analysis.total_calorie is not None) else None
        }


class MarginAnalyzer:
    @staticmethod
    def analyze_by_category(analyses: List[DishCostAnalysis]) -> Dict[str, Dict]:
        category_stats: Dict[str, Dict] = {}

        for analysis in analyses:
            category = analysis.dish.category
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'total_margin': 0.0,
                    'avg_margin': 0.0,
                    'dishes': []
                }

            category_stats[category]['count'] += 1
            category_stats[category]['total_margin'] += analysis.gross_margin
            category_stats[category]['dishes'].append(analysis)

        for category, stats in category_stats.items():
            stats['avg_margin'] = stats['total_margin'] / stats['count'] if stats['count'] > 0 else 0

        return category_stats

    @staticmethod
    def get_low_margin_dishes(analyses: List[DishCostAnalysis], threshold: float = 0.4) -> List[DishCostAnalysis]:
        return [analysis for analysis in analyses if analysis.gross_margin < threshold]
