from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .constants import MAX_LENGHT, MINIMAL_TIME

User = get_user_model()


class Ingredient (models.Model):
    name = models.CharField(max_length=MAX_LENGHT, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=MAX_LENGHT,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_ingredients'
        ),)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag (models.Model):
    name = models.CharField(max_length=MAX_LENGHT, verbose_name='Название')
    slug = models.SlugField(
        max_length=MAX_LENGHT,
        unique=True,
        verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe (models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Продукты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    name = models.CharField(max_length=MAX_LENGHT, verbose_name='Название')
    text = models.TextField('Описание')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        auto_now=True,
        db_index=True
    )
    cooking_time = models.IntegerField(
        validators=[
            MinValueValidator(MINIMAL_TIME)
        ],
        default=MINIMAL_TIME,
        verbose_name='Время приготовления, минуты'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient (models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MINIMAL_TIME)], default=MINIMAL_TIME
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        constraints = (models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_recipeingredients'
        ),)


class FavoriteShopingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True


class Favorite(FavoriteShopingCart):

    class Meta(FavoriteShopingCart.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('user',)
        constraints = (models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_favorite_recipe'
        ),)

    def __str__(self):
        return f'{self.recipe.name} добавлен в избранное {self.user.username}'


class ShopingCart(FavoriteShopingCart):

    class Meta(FavoriteShopingCart.Meta):
        default_related_name = 'shopingcart'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('user',)
        constraints = (models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_shopingcart'
        ),)

    def __str__(self):
        return f'{self.recipe.name} добавлен в корзину {self.user.username}'
