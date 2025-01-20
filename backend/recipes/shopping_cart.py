import datetime as dt

from django.db.models import Sum

from recipes.models import RecipeIngredient, ShopingCart

DELIMETER = '\n'

REPORT_NAME = 'Список покупок'

INGREDIENTS_LIST = 'Список продуктов'

INGREDIENTS_COLUMNS = '№\tПродукт\tМера\tЕдиница измерения'

RECIPES_LIST = 'Список рецептов'


def form_shopping_cart(request):
    date = dt.date.today().strftime('%d-%m-%y')
    shoping_cart = ShopingCart.objects.filter(
        user=request.user
    ).values('recipe', 'recipe__name')
    recipes = [item['recipe'] for item in shoping_cart]
    recipes_names = [item['recipe__name'] for item in shoping_cart]
    ingredients = RecipeIngredient.objects.filter(
        recipe__in=recipes
    ).values(
        'ingredient__name',
        'ingredient__measurement_unit'
    ).annotate(
        amount=Sum('amount')
    ).order_by('ingredient__name')
    ingredients_to_text = DELIMETER.join([
        f"{number}\t{ingredient['ingredient__name']}"
        f"\t{ingredient['amount']}"
        f"\t{ingredient['ingredient__measurement_unit']}"
        for number, ingredient in enumerate(ingredients)
    ])
    recipes_to_text = DELIMETER.join([
        f'{number}\t{name}' for number, name in enumerate(recipes_names)
    ])
    return DELIMETER.join([
        date,
        REPORT_NAME,
        INGREDIENTS_LIST,
        INGREDIENTS_COLUMNS,
        ingredients_to_text,
        RECIPES_LIST,
        recipes_to_text
    ])
