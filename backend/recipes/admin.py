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
    VALUES = (
        ('quick', 'Быстрее 5 мин.'),
        ('middle', 'Быстрее 30 мин.'),
        ('long', 'Долго')
    )
    MIDDLE_BORDER = 5
    LONG_BORDER = 30
    QUERYSET_VALUES = dict(
        quick=(0, MIDDLE_BORDER),
        middle=(MIDDLE_BORDER + 1, LONG_BORDER),
        long=(LONG_BORDER + 1, 10**10)
    )

    def lookups(self, request, model_admin):
        return self.VALUES

    def queryset(self, request, queryset):
        if self.value() in self.QUERYSET_VALUES:
            return queryset.filter(
                cooking_time__range=self.QUERYSET_VALUES.get(self.value())
            )
        return queryset


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
        return '<br>'.join(recipe.tags.values_list('name', flat=True))

    def ingredients_override(self, recipe):
        return '<br>'.join([
            '{ingredient__name} {ingredient__measurement_unit} {amount}'
            .format(**ingredient) for ingredient in RecipeIngredient
            .objects.filter(recipe=recipe).values(
                'ingredient__name', 'ingredient__measurement_unit', 'amount'
            )
        ])

    @admin.display(description='Изображение')
    @mark_safe
    def image(self, recipe):
        return f'<img src="{recipe.image.file}">'


class UserSimpleListFilter(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        return self.VALUES

    def queryset(self, request, queryset):
        if self.value() in self.QUERYSET_VALUES:
            return queryset.distinct().filter(
                **self.QUERYSET_VALUES.get(self.value())
            )
        return queryset


class FollowersFilter(UserSimpleListFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'followers_count'
    VALUES = (
        ('lt_1', 'Нет подписчиков'),
        ('gt_1', 'Есть подписчики'),
    )
    QUERYSET_VALUES = dict(
        lt_1={'followers__isnull': True},
        gt_1={'followers__isnull': False}
    )


class AuthorsFilter(UserSimpleListFilter):
    title = 'Наличие подписок'
    parameter_name = 'authors_count'
    VALUES = (
        ('lt_1', 'Нет подписок'),
        ('gt_1', 'Есть подписки'),
    )
    QUERYSET_VALUES = dict(
        lt_1={'authors__isnull': True},
        gt_1={'authors__isnull': False}
    )


class RecipesFilter(UserSimpleListFilter):
    title = 'Наличие рецептов'
    parameter_name = 'recipe_count'
    VALUES = (
        ('lt_1', 'Нет рецептов'),
        ('gt_1', 'Есть рецепты'),
    )
    QUERYSET_VALUES = dict(
        lt_1={'recipes__isnull': True},
        gt_1={'recipes__isnull': False}
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
        return f'<img src="{user.avatar.file}">'
