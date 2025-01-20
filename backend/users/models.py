from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .constants import MAX_LENGHT, MAX_LENGHT_EMAIL


class FoodgramUser(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=MAX_LENGHT_EMAIL
    )
    avatar = models.ImageField(
        upload_to='users/', null=True, blank=True
    )
    username = models.CharField(
        verbose_name='Логин', max_length=MAX_LENGHT, unique=True,
        validators=[
            RegexValidator(regex=r'[^\w.@+-]', inverse_match=True)
        ]
    )
    first_name = models.CharField(
        verbose_name='Имя', max_length=MAX_LENGHT
    )
    last_name = models.CharField(
        verbose_name='Фамилия', max_length=MAX_LENGHT
    )
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
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
        related_name='followers',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        FoodgramUser,
        verbose_name='Автор',
        related_name='authors',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('follower', 'author'),
                name='unique_subscription'
            ),
        )

    def __str__(self):
        return f'{self.follower} подписался на {self.author}'
