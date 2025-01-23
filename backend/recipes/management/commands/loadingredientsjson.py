import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Начало загрузки файлов'

    def handle(self, *args, **options):
        with open(
            'data/ingredients.json',
            'r',
            encoding='utf-8'
        ) as ingredient_file:
            ingredients = json.load(ingredient_file)
            ingredients_created = Ingredient.objects.bulk_create(
                (Ingredient(**ingredient) for ingredient in ingredients),
                ignore_conflicts=True
            )
            self.stdout.write(
                f'Загружено {len(ingredients_created)} продуктов'
            )
