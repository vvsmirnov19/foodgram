from django.contrib.auth.models import AbstractUser
from django.db import models


class FoodgramUser(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=255
    )
    avatar = models.ImageField(
        upload_to='users/', null=True, blank=True
    )
    username = models.CharField(
        verbose_name='Логин', max_length=150, unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=150
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=150
    )
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Subscription(models.Model):
    follower = models.ForeignKey(
        FoodgramUser,
        verbose_name='Подписчик',
        related_name='subscripted',
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        FoodgramUser,
        verbose_name='Автор',
        related_name='subscripting',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('follower', 'following'),
                name='unique_subscription'
            ),
        )

    def __str__(self):
        return self.following
