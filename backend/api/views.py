import os

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilterSet, RecipeFilterSet
from api.paginators import FoodgramPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FoodgramUserSerializer, IngredientSerializer,
                             ReadRecipeSerializer, RecipeSerializer,
                             SmallRecipeSerializer, SubscribeSerializer,
                             TagSerializer)
from recipes.models import (Favorite, Ingredient, Recipe,
                            ShopingCart, Tag)
from recipes.shopping_cart import form_shopping_cart
from users.models import Subscription

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilterSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = (
        IsAuthorOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly
    )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadRecipeSerializer
        return RecipeSerializer

    @staticmethod
    def favorite_and_shopping_add(pk, model, request, message):
        recipe = get_object_or_404(Recipe, id=pk)
        item = model.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if item.exists():
            raise ValidationError(f'Данный рецепт уже в {message}!')
        created_item = model.objects.create(
            user=request.user,
            recipe=recipe
        )
        return Response(
            SmallRecipeSerializer(created_item.recipe).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def favorite_and_shopping_delete(pk, model, request, message):
        recipe = get_object_or_404(Recipe, id=pk)
        item = model.objects.filter(
            user=request.user,
            recipe=recipe
        ).first()
        if not item:
            raise ValidationError(f'Рецепта нет в {message}!')
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self.favorite_and_shopping_add(
            pk, Favorite, request, 'избранном'
        )

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        return self.favorite_and_shopping_delete(
            pk, Favorite, request, 'избранном'
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        return self.favorite_and_shopping_add(
            pk, ShopingCart, request, 'корзине'
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        return self.favorite_and_shopping_delete(
            pk, ShopingCart, request, 'корзине'
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        return FileResponse(
            form_shopping_cart(request),
            as_attachment=True,
            filename='cart.txt'
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[permissions.AllowAny]
    )
    def get_link(self, request, pk):
        if not Recipe.objects.filter(id=pk).exists():
            raise ValidationError(
                'Такого рецепта не существует!'
            )
        return Response({'short-link': request.build_absolute_uri(f'/s/{pk}')},
                        status=status.HTTP_200_OK)


class FoodgramUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = FoodgramPagination
    permission_classes = []

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated(),]
        return super().get_permissions()

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['put'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        if not request.data.get('avatar'):
            raise ValidationError('Отсутсвует файл!')
        serializer = FoodgramUserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid()
        serializer.save()
        return Response(
            {'avatar': serializer.data['avatar']},
            status=status.HTTP_200_OK
        )

    @avatar.mapping.delete
    def avatar_delete(self, request):
        if request.user.avatar is None:
            raise ValidationError('Аватар не установлен!')
        filepath = str(request.user.avatar.file)
        request.user.avatar = None
        request.user.save()
        os.remove(filepath)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        recipes_limit = request.query_params.get('recipes_limit')
        subscriptions_items = request.user.followers.all()
        subscriptions = [
            subscription.author for subscription in subscriptions_items
        ]
        paginator = self.paginate_queryset(subscriptions)
        serializer = SubscribeSerializer(
            paginator,
            context={'request': request, 'recipes_limit': recipes_limit},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if author.id == request.user.id:
            raise ValidationError('Нельзя подписаться на самого себя!')
        subscription = Subscription.objects.filter(
            follower=request.user,
            author=author
        )
        if subscription.exists():
            raise ValidationError('Вы уже подписаны на этого пользователя!')
        created_subscription = Subscription.objects.create(
            follower=request.user,
            author=author
        ).author
        return Response(
            SubscribeSerializer(
                created_subscription,
                context={
                    'request': request,
                }
            ).data, status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id):
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            follower=request.user,
            author=author
        )
        if not subscription.exists():
            raise ValidationError(
                'Вы не были подписаны на этого пользователя!'
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
