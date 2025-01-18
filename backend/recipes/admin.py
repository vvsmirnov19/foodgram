from django.contrib import admin

from recipes.models import (
    Ingredient,
    Favorite,
    Recipe,
    ShopingCart,
    Tag
)


@admin.register(Ingredient)
class IngridientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', )
    search_fields = ['name']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favorite_count', 'tags_override', )
    search_fields = ['name', 'author']
    list_filter = ['tags']

    def favorite_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    def tags_override(self, obj):
        return ', '.join(obj.tags.values_list('name', flat=True))


@admin.register(ShopingCart)
class ShopingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', )
