import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from users.serializers import FoodgramUserSerializer

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    author = FoodgramUserSerializer(read_only=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
        )

    def create(self, validated_data):
        recipe = Recipe.objects.create(
            author=self.context.get('request').user,
            image=validated_data.pop('image'),
            name=validated_data.pop('name'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time')
        )
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient.get('ingredient'),
            amount=ingredient.get('amount')
        ) for ingredient in ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('recipe_ingredients', None)
        tags = validated_data.pop('tags', None)
        self.validate_ingredients(ingredients)
        self.validate_tags(tags)
        instance.tags.set(tags)
        RecipeIngredient.objects.bulk_create(RecipeIngredient(
            recipe=instance,
            ingredient=ingredient.get('ingredient'),
            amount=ingredient.get('amount')
        ) for ingredient in ingredients)
        return super().update(instance, validated_data)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Отсутствуют ингридиенты!')
        ingredient_ids = set()
        for ingredient in value:
            ingredient_id = ingredient['ingredient'].id
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    'Дублируются ингридиенты!')
            ingredient_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Отсутствуют теги!')
        tags = set()
        for tag in value:
            if tag in tags:
                raise serializers.ValidationError(
                    'Дублируются теги!')
            tags.add(tag)
        return value

    def validate(self, value):
        if value.get('cooking_time') < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше 1!')
        return value

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    author = FoodgramUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user and not user.is_anonymous:
            return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user and not user.is_anonymous:
            return obj.shopingcart.filter(user=user).exists()
        return False


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, attrs):
        recipe = get_object_or_404(Recipe, id=self.context['id'])
        if recipe.favorites.filter(user=self.context['request'].user).exists():
            raise serializers.ValidationError('Рецепт уже в избранном!')
        return attrs

    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, id=self.context['id'])
        favorite = self.context['request'].user.favorites.create(recipe=recipe)
        return favorite.recipe

    def delete(self, user):
        recipe = get_object_or_404(Recipe, id=self.context['id'])
        favorite = user.favorites.filter(recipe=recipe).first()
        if not favorite:
            raise serializers.ValidationError('Рецепта нет в избранном!')
        favorite.delete()


class ShopingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, attrs):
        recipe = get_object_or_404(Recipe, id=self.context['id'])
        if recipe.shopingcart.filter(
            user=self.context['request'].user
        ).exists():
            raise serializers.ValidationError('Рецепт уже в корзине!')
        return attrs

    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, id=self.context['id'])
        cart = self.context['request'].user.shopingcart.create(recipe=recipe)
        return cart.recipe

    def delete(self, user):
        recipe = get_object_or_404(Recipe, id=self.context['id'])
        cart = user.shopingcart.filter(recipe=recipe).first()
        if not cart:
            raise serializers.ValidationError('Рецепта нет в корзине!')
        cart.delete()
