from pydantic import BaseModel
from typing import List

class IngredientExpansionRequest(BaseModel):
    ingredients: List[str]

class IngredientExpansionResponse(BaseModel):
    expanded_ingredients: List[str]

class RecipeMatchRequest(BaseModel):
    recipe_ingredients: List[str]
    input_ingredients: List[str]

class RecipeMatchResponse(BaseModel):
    match_ratio: float
    matched_ingredients: List[str]
    missing_ingredients: List[str]

class SmartRecipeRequest(BaseModel):
    ingredients: List[str]
    recipes: List[str]

class SmartRecipeResponse(BaseModel):
    best_recipe: str
    reasons: str
