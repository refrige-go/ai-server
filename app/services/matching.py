from app.models.schemas import RecipeMatchRequest, RecipeMatchResponse

async def match_recipe_ingredients(request: RecipeMatchRequest) -> RecipeMatchResponse:
    matched = [i for i in request.recipe_ingredients if i in request.input_ingredients]
    missing = [i for i in request.recipe_ingredients if i not in request.input_ingredients]
    ratio = len(matched) / len(request.recipe_ingredients) if request.recipe_ingredients else 0
    return RecipeMatchResponse(
        match_ratio=ratio,
        matched_ingredients=matched,
        missing_ingredients=missing
    )
