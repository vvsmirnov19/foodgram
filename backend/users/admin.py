from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser


@admin.register(FoodgramUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name',
                    'last_name', 'password')
    search_fields = ('email', 'username',)
    ordering = ('username',)
