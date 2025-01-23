import json

from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Начало загрузки файлов'

    def handle(self, *args, **options):
        with open('data/tags.json', 'r', encoding='utf-8') as tag_file:
            tags = json.load(tag_file)
            tags_created = Tag.objects.bulk_create(
                (Tag(**tag) for tag in tags),
                ignore_conflicts=True)
            self.stdout.write(f'Загружено {len(tags_created)} тегов')
