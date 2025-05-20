from app.models.schemas import SmartRecipeRequest, SmartRecipeResponse
from app.core.ai import get_llm, smart_recommendation_prompt

async def smart_recipe_recommendation(request: SmartRecipeRequest) -> SmartRecipeResponse:
    prompt = smart_recommendation_prompt(request.ingredients, request.recipes)
    llm = get_llm()
    response = llm.invoke(prompt)
    best_recipe, reasons = response.content.split("이유:")
    return SmartRecipeResponse(
        best_recipe=best_recipe.strip(),
        reasons=reasons.strip()
    )
