from app.models.schemas import IngredientExpansionRequest, IngredientExpansionResponse
from app.core.ai import get_llm, expand_ingredients_prompt

async def expand_ingredients(request: IngredientExpansionRequest) -> IngredientExpansionResponse:
    prompt = expand_ingredients_prompt(request.ingredients)
    llm = get_llm()
    response = llm.invoke(prompt)
    expanded = [ingredient.strip() for ingredient in response.content.split(",")]
    return IngredientExpansionResponse(expanded_ingredients=expanded)
