from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.safestring import mark_safe

from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShopingCart, Tag)


User = get_user_model()

admin.site.unregister(Group)


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
        queriset_values = dict(
            quick=(1, 5),
            middle=(6, 30),
            long=(31, max(queryset.values_list('cooking_time', flat=True)))
        )
        return queryset.filter(
            cooking_time__range=queriset_values.get(self.value)
        )


class RecipeCountMixin():

    @admin.display(description='Рецепты')
    def recipe_count(self, model):
        return model.recipes.count()


@admin.register(Ingredient)
class IngridientAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit',)


class IngredientsInLine(admin.StackedInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
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
        return '\n'.join(recipe.tags.values_list('name', flat=True))

    def ingredients_override(self, recipe):
        return '\n'.join('{name} {measurment_unit} {amount}'.format(
            **recipe.ingredients.values('name', 'measurment_unit', 'amount')
        ))

    @admin.display(description='Изображение')
    @mark_safe
    def avatar(self, recipe):
        return recipe.image.file


class UserSimpleListFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        return self.values

    def queryset(self, request, queryset):
        return queryset.filter(**self.queriset_values.get(self.value))


class FollowersFilter(UserSimpleListFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'followers_count'
    values = (
        ('lt_1', 'Нет подписчиков'),
        ('gt_1', 'Есть подписчики'),
    )
    queriset_values = dict(
        lt_1={'followers_count__lt': 1},
        gt_1={'followers_count__gt': 1}
    )


class AuthorsFilter(UserSimpleListFilter):
    title = 'Наличие подписок'
    parameter_name = 'authors_count'
    values = (
        ('lt_1', 'Нет подписок'),
        ('gt_1', 'Есть подписки'),
    )
    queriset_values = dict(
        lt_1={'authors_count__lt': 1},
        gt_1={'authors_count__gt': 1}
    )


class RecipesFilter(UserSimpleListFilter):
    title = 'Наличие рецептов'
    parameter_name = 'recipe_count'
    values = (
        ('lt_1', 'Нет рецептов'),
        ('gt_1', 'Есть рецепты'),
    )
    queriset_values = dict(
        lt_1={'recipe_count__lt': 1},
        gt_1={'recipe_count__gt': 1}
    )


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'username', 'full_name',
                    'password', 'avatar', 'followers_count',
                    'authors_count', 'recipe_count')
    search_fields = ('email', 'username',)
    list_filter = (FollowersFilter, AuthorsFilter, RecipesFilter)
    ordering = ('username',)

    @admin.display(description='Полное имя')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Подписчики')
    def followers_count(self, user):
        return user.followers.count()

    @admin.display(description='Подписки')
    def authors_count(self, user):
        return user.authors.count()

    @admin.display(description='Рецепты')
    @mark_safe
    def recipe_count(self, user):
        count = user.recipes.count()
        if count > 0:
            url = f'{reverse("api:recipes-list")}?author={user.id}'
            return f'<a href="{url}">{count}</a>'
        return count

    @admin.display(description='Аватар')
    @mark_safe
    def avatar(self, user):
        return user.avatar.file
