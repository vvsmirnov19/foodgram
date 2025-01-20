from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe


User = get_user_model()

admin.site.unregister(Group)


class FollowersFilter(admin.SimpleListFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'followers_count'

    def lookups(self, request, model_admin):
        return (
            ('lt_1', 'Нет подписчиков'),
            ('gt_1', 'Есть подписчики'),
        )

    def queryset(self, request, queryset):
        value = self.value
        if value == 'lt_1':
            return queryset.filter(followers_count__lt=1)
        elif value == 'gt_1':
            return queryset.filter(followers_count__gt=1)
        return queryset


class AuthorsFilter(admin.SimpleListFilter):
    title = 'Наличие подписок'
    parameter_name = 'authors_count'

    def lookups(self, request, model_admin):
        return (
            ('lt_1', 'Нет подписок'),
            ('gt_1', 'Есть подписки'),
        )

    def queryset(self, request, queryset):
        value = self.value
        if value == 'lt_1':
            return queryset.filter(authors_count__lt=1)
        elif value == 'gt_1':
            return queryset.filter(authors_count__gt=1)
        return queryset


class RecipesFilter(admin.SimpleListFilter):
    title = 'Наличие рецептов'
    parameter_name = 'recipe_count'

    def lookups(self, request, model_admin):
        return (
            ('lt_1', 'Нет рецептов'),
            ('gt_1', 'Есть рецепты'),
        )

    def queryset(self, request, queryset):
        value = self.value
        if value == 'lt_1':
            return queryset.filter(recipe_count__lt=1)
        elif value == 'gt_1':
            return queryset.filter(recipe_count__gt=1)
        return queryset


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
        return ' '.join([user.first_name, user.last_name])

    @admin.display(description='Количество подписчиков')
    def followers_count(self, user):
        return user.followers.count()

    @admin.display(description='Количество подписок')
    def authors_count(self, user):
        return user.authors.count()

    @admin.display(description='Количество рецептов')
    def recipe_count(self, user):
        count = user.recipes.count()
        url = f'{reverse("api:recipes-list")}?author={user.id}'
        if count > 1:
            return format_html(f'<a href="{url}">{count}</a>')
        return count

    @admin.display(description='Аватар')
    @mark_safe
    def avatar(self, user):
        return str(user.avatar.file)
