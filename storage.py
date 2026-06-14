import json
import os
from typing import List, Dict, Optional
from models import Ingredient, Dish


class DataStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ingredients_file = os.path.join(data_dir, "ingredients.json")
        self.dishes_file = os.path.join(data_dir, "dishes.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def save_ingredients(self, ingredients: Dict[str, Ingredient]) -> None:
        data = [ingredient.to_dict() for ingredient in ingredients.values()]
        with open(self.ingredients_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_ingredients(self) -> Dict[str, Ingredient]:
        if not os.path.exists(self.ingredients_file):
            return {}
        
        with open(self.ingredients_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ingredients = {}
        for item in data:
            ingredient = Ingredient.from_dict(item)
            ingredients[ingredient.id] = ingredient
        return ingredients

    def save_dishes(self, dishes: List[Dish]) -> None:
        data = [dish.to_dict() for dish in dishes]
        with open(self.dishes_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_dishes(self) -> List[Dish]:
        if not os.path.exists(self.dishes_file):
            return []
        
        with open(self.dishes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return [Dish.from_dict(item) for item in data]

    def get_ingredient_by_name(self, name: str, ingredients: Dict[str, Ingredient]) -> Optional[Ingredient]:
        for ingredient in ingredients.values():
            if ingredient.name == name:
                return ingredient
        return None

    def get_dish_by_name(self, name: str, dishes: List[Dish]) -> Optional[Dish]:
        for dish in dishes:
            if dish.name == name:
                return dish
        return None
