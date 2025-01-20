from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.constants import MINIMAL_COOKING_TIME
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShopingCart, Tag)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'
    max_time = max(Recipe.objects.values_list('cooking_time', flat=True))
    min_time = MINIMAL_COOKING_TIME
    difference = max_time - min_time
    second_time = int(min_time + difference / 3)
    quick_time_count = Recipe.objects.filter(
        cooking_time__lt=second_time
    ).count()
    third_time = int(min_time + difference * 2 / 3)
    middle_time_count = Recipe.objects.filter(
        cooking_time__lt=third_time
    ).count()
    long_count = Recipe.objects.filter(cooking_time__gt=third_time).count()

    def lookups(self, request, model_admin):
        return (
            ('quick', f'Быстрее {self.second_time} ({self.quick_time_count})'),
            ('middle',
             f'Быстрее {self.third_time} ({self.middle_time_count})'),
            ('long', f'Долго ({self.long_count})')
        )

    def queryset(self, request, queryset):
        value = self.value
        if value == 'quick':
            return queryset.filter(cooking_time__lt=self.second_time)
        elif value == 'middle':
            return queryset.filter(cooking_time__lt=self.third_time)
        elif value == 'long':
            return queryset.filter(cooking_time__gt=self.third_time)
        return queryset


class RecipeCountMixin(admin.ModelAdmin):

    @admin.display(description='Количество рецептов')
    def recipe_count(self, model):
        return model.recipes.count()


@admin.register(Ingredient)
class IngridientAdmin(RecipeCountMixin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    list_filter = ('name', 'measurement_unit',)
    search_fields = ('name', 'measurement_unit',)


class IngredientsInLine(admin.StackedInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(RecipeCountMixin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug', )


@admin.register(Favorite, ShopingCart)
class FavoriteAndCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorite_count', 'tags_override',
                    'ingredients_override', 'cooking_time', 'image')
    search_fields = ['name', 'author', 'tags']
    list_filter = ['tags', 'author', CookingTimeFilter]
    inlines = (IngredientsInLine, )

    def favorite_count(self, recipe):
        return recipe.favorites.count()

    def tags_override(self, recipe):
        return ', '.join(recipe.tags.values_list('name', flat=True))

    def ingredients_override(self, recipe):
        return ', '.join(recipe.ingredients.values_list('name', flat=True))

    @admin.display(description='Изображение')
    @mark_safe
    def avatar(self, recipe):
        return str(recipe.image.file)
