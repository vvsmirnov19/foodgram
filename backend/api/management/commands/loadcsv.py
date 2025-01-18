from csv import reader

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag


def load_ingridients(row):
    Ingredient.objects.create(name=row[0], measurement_unit=row[1])


def load_tags(row):
    Tag.objects.create(name=row[0], slug=row[1])


files = (('data/ingredients.csv', load_ingridients),
         ('data/tags.csv', load_tags))


class Command(BaseCommand):
    help = 'Начало загрузки файлов'

    def handle(self, *args, **options):
        for file, function in files:
            with open(file, 'r', encoding='utf-8') as current_file:
                content = reader(current_file)
                for row in content:
                    function(row)
                self.stdout.write('Загрузка завершена')
