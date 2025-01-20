import re

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MINIMAL_AMOUNT, MINIMAL_COOKING_TIME
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscription


User = get_user_model()


class FoodgramUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField(default=False)

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('avatar', 'is_subscribed')

    def validate_username(username):
        if not re.search(r'[^\w.@+-]', username):
            raise serializers.ValidationError(
                f'Недопустимый username {username}.'
            )
        return username

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Subscription.objects.filter(
                follower=request.user, author=author
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(min_value=MINIMAL_AMOUNT)

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
    cooking_time = serializers.IntegerField(min_value=MINIMAL_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
        )

    @staticmethod
    def handling_tags_ingredient(recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient['ingredient'],
            amount=ingredient['amount']
        ) for ingredient in ingredients)

    def create(self, validated_data):
        validated_data.update(author=self.context.get('request').user)
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = super().create(validated_data)
        self.handling_tags_ingredient(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = validated_data.pop('recipe_ingredients', None)
        tags = validated_data.pop('tags', None)
        self.validate_ingredients(ingredients)
        self.validate_tags(tags)
        self.handling_tags_ingredient(instance, tags, ingredients)
        return super().update(instance, validated_data)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Отсутствуют продукты!')
        ingredient_ids = set()
        for ingredient in value:
            ingredient_id = ingredient['ingredient'].id
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    f'Дублируется продукт {ingredient_id}!')
            ingredient_ids.add(ingredient_id)
        return value

    def validate_tags(self, tags_data):
        if not tags_data:
            raise serializers.ValidationError('Отсутствуют теги!')
        tags = set()
        for tag in tags_data:
            if tag in tags:
                raise serializers.ValidationError(
                    f'Дублируется тег {tag}!')
            tags.add(tag)
        return tags_data

    def validate_image(self, image_data):
        if not image_data:
            raise serializers.ValidationError(
                'Нет изображения!')
        return image_data

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    author = FoodgramUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(default=False)
    is_in_shopping_cart = serializers.SerializerMethodField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'author',
            'ingredients', 'tags', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        return (
            user is not None
            and not user.is_anonymous
            and recipe.favorites.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        return (
            user is not None
            and not user.is_anonymous
            and recipe.shopingcart.filter(user=user).exists()
        )


class SmallRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(FoodgramUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = FoodgramUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )
        read_only_fields = ('id',)

    def get_recipes(self, author):
        return SmallRecipeSerializer(
            author.recipes.all()[:int(self.context.get(
                'request'
            ).query_params.get('recipes_limit', '100000'))],
            many=True,
            context={'request': self.context.get('request')}
        ).data
