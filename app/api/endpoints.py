from fastapi import APIRouter
from app.services.expansion import expand_ingredients
from app.services.matching import match_recipe_ingredients
from app.services.recommendation import smart_recipe_recommendation
from app.models.schemas import (
    IngredientExpansionRequest, IngredientExpansionResponse,
    RecipeMatchRequest, RecipeMatchResponse,
    SmartRecipeRequest, SmartRecipeResponse
)

router = APIRouter(prefix="/ai")

@router.get("/health")
def health_check():
    return {"status": "healthy"}

@router.post("/ingredients/expand", response_model=IngredientExpansionResponse)
async def expand(request: IngredientExpansionRequest):
    return await expand_ingredients(request)

@router.post("/recipe/match", response_model=RecipeMatchResponse)
async def match(request: RecipeMatchRequest):
    return await match_recipe_ingredients(request)

@router.post("/recipes/smart-recommend", response_model=SmartRecipeResponse)
async def smart_recommend(request: SmartRecipeRequest):
    return await smart_recipe_recommendation(request)
