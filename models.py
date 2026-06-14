from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import uuid


@dataclass
class PriceHistory:
    price: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'price': self.price,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PriceHistory':
        return cls(
            price=data['price'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class Ingredient:
    name: str
    unit: str
    current_price: float
    calorie_per_unit: Optional[float] = None
    price_history: List[PriceHistory] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if not self.price_history:
            self.price_history.append(PriceHistory(price=self.current_price))

    def update_price(self, new_price: float) -> None:
        self.current_price = new_price
        self.price_history.append(PriceHistory(price=new_price))

    def get_unit_conversion(self, recipe_unit: str, recipe_amount: float) -> float:
        unit_conversions = {
            ('kg', 'g'): 0.001,
            ('kg', 'kg'): 1.0,
            ('L', 'ml'): 0.001,
            ('L', 'L'): 1.0,
            ('g', 'g'): 1.0,
            ('g', 'kg'): 1000.0,
            ('ml', 'ml'): 1.0,
            ('ml', 'L'): 1000.0,
            ('个', '个'): 1.0,
            ('把', '把'): 1.0,
            ('片', '片'): 1.0,
        }
        key = (self.unit, recipe_unit)
        if key not in unit_conversions:
            raise ValueError(f"不支持的单位转换: {self.unit} -> {recipe_unit}")
        return recipe_amount * unit_conversions[key]

    def calculate_cost(self, amount: float, unit: str) -> float:
        converted_amount = self.get_unit_conversion(unit, amount)
        return converted_amount * self.current_price

    def calculate_calorie(self, amount: float, unit: str) -> Optional[float]:
        if self.calorie_per_unit is None:
            return None
        converted_amount = self.get_unit_conversion(unit, amount)
        return converted_amount * self.calorie_per_unit

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'current_price': self.current_price,
            'calorie_per_unit': self.calorie_per_unit,
            'price_history': [ph.to_dict() for ph in self.price_history]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Ingredient':
        return cls(
            id=data['id'],
            name=data['name'],
            unit=data['unit'],
            current_price=data['current_price'],
            calorie_per_unit=data.get('calorie_per_unit'),
            price_history=[PriceHistory.from_dict(ph) for ph in data['price_history']]
        )


@dataclass
class RecipeItem:
    ingredient_id: str
    ingredient_name: str
    amount: float
    unit: str

    def to_dict(self) -> Dict:
        return {
            'ingredient_id': self.ingredient_id,
            'ingredient_name': self.ingredient_name,
            'amount': self.amount,
            'unit': self.unit
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RecipeItem':
        return cls(
            ingredient_id=data['ingredient_id'],
            ingredient_name=data['ingredient_name'],
            amount=data['amount'],
            unit=data['unit']
        )


@dataclass
class Dish:
    name: str
    category: str
    recipe: List[RecipeItem]
    target_margin: float = 0.6
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'target_margin': self.target_margin,
            'recipe': [item.to_dict() for item in self.recipe]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Dish':
        return cls(
            id=data['id'],
            name=data['name'],
            category=data['category'],
            target_margin=data.get('target_margin', 0.6),
            recipe=[RecipeItem.from_dict(item) for item in data['recipe']]
        )


@dataclass
class DishCostAnalysis:
    dish: Dish
    material_cost: float
    suggested_price: float
    gross_profit: float
    gross_margin: float
    total_calorie: Optional[float]
    ingredient_costs: List[Tuple[str, float]]

    def to_dict(self) -> Dict:
        return {
            'dish_id': self.dish.id,
            'dish_name': self.dish.name,
            'category': self.dish.category,
            'material_cost': round(self.material_cost, 2),
            'suggested_price': round(self.suggested_price, 2),
            'gross_profit': round(self.gross_profit, 2),
            'gross_margin': round(self.gross_margin * 100, 2),
            'total_calorie': round(self.total_calorie, 2) if self.total_calorie else None,
            'ingredient_costs': [(name, round(cost, 2)) for name, cost in self.ingredient_costs]
        }
