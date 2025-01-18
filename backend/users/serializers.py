import base64
import re

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import serializers

from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class FoodgramUserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField(default=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')
        read_only_fields = ('id',)

    def validate_username(username):
        if not re.search(r'[^\w.@+-]', username):
            raise serializers.ValidationError(
                'Недопустимый username.'
            )
        return username

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscripting.filter(follower=request.user).exists()
        return False


class SmallRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(FoodgramUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'avatar', 'is_subscribed',
                  'recipes', 'recipes_count')
        read_only_fields = ('id',)

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        print(recipes_limit)
        queryset = obj.recipes.all()
        if recipes_limit is not None:
            queryset = obj.recipes.all()[:int(recipes_limit)]
            print(queryset)
        return SmallRecipeSerializer(
            queryset,
            many=True,
            context={'request': self.context.get('request')}
        ).data

    def get_recipes_count(self, obj):
        return len(obj.recipes.all())

    def create(self, validated_data):
        follower = self.context['request'].user
        following = get_object_or_404(User, id=self.context['id'])
        subscription = Subscription.objects.create(
            follower=follower,
            following=following
        )
        return subscription.following

    def delete(self, user):
        following = get_object_or_404(User, id=self.context['id'])
        subscription = Subscription.objects.get(
            follower=user,
            following=following
        )
        if not subscription:
            raise serializers.ValidationError(
                'Такого пользователя не существует!'
            )
        subscription.delete()


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs.get('current_password')):
            raise serializers.ValidationError('Введен неверный пароль')
        return attrs
