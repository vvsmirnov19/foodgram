import datetime as dt

DELIMETER = '\n'

REPORT_NAME = 'Список покупок'

INGREDIENTS_LIST = 'Список продуктов'

INGREDIENTS_COLUMNS = '№, Продукт, Мера, Единица измерения'

RECIPES_LIST = 'Список рецептов'

TEMPLATE_INGREDIENTS = '{}. {} {} {}.'

TEMPLATE_RECIPES = '{}. {}'


def form_shopping_cart(recipes_names, ingredients):
    date = dt.date.today().strftime('%d %B %Y')
    ingredients_to_text = DELIMETER.join([
        TEMPLATE_INGREDIENTS.format(
            number,
            ingredient['ingredient__name'].capitalize(),
            ingredient['amount'],
            ingredient['ingredient__measurement_unit']
        ) for number, ingredient in enumerate(ingredients, 1)
    ])
    recipes_to_text = DELIMETER.join(
        (TEMPLATE_RECIPES.format(
            number, name
        ) for number, name in enumerate(recipes_names, 1))
    )
    return DELIMETER.join([
        date,
        REPORT_NAME,
        INGREDIENTS_LIST,
        INGREDIENTS_COLUMNS,
        ingredients_to_text,
        RECIPES_LIST,
        recipes_to_text
    ])
