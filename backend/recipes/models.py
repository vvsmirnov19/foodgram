from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models


User = get_user_model()


class Ingredient (models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=255,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag (models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(
        max_length=255,
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
        verbose_name='Автор',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингридиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    text = models.TextField('Описание')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        auto_now=True,
        db_index=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                1,
                'Время приготовления не может быть меньше 1'
            )
        ],
        default=1,
        verbose_name='Время приготовления'
    )
    is_favorited = models.BooleanField(
        default=False,
        verbose_name='В избранном'
    )
    is_in_shopping_cart = models.BooleanField(
        default=False,
        verbose_name='В списке покупок'
    )
    link = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Короткая ссылка"
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class RecipeIngredient (models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            1,
            'Количество не может быть меньше 1'
        )],
        default=1
    )


class RecipeTag (models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_favorite_recipe'
        ),)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('user',)

    def __str__(self):
        return f'{self.recipe}'


class ShopingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopingcart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopingcart',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = (models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_shopingcart'
        ),)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('user',)

    def __str__(self):
        return f'{self.recipe}'
