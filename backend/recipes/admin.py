from django.contrib import admin
from django.utils.safestring import mark_safe

from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShopingCart, Tag)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        return (
            ('quick', 'Быстрее 5 мин.'),
            ('middle',
             'Быстрее 30 мин.'),
            ('long', 'Долго')
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
