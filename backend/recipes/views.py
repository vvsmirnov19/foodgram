from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.paginators import FoodgramPagination

from recipes.filters import IngredientFilterSet, RecipeFilterSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShopingCart, Tag)
from recipes.permissions import IsAuthorOrReadOnly
from recipes.serializers import (FavoriteSerializer, IngredientSerializer,
                                 ReadRecipeSerializer, RecipeSerializer,
                                 ShopingCartSerializer, TagSerializer)


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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite_item = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if favorite_item.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = FavoriteSerializer(
            data={},
            context={'request': request, 'id': pk}
        )
        serializer.is_valid()
        favorite = serializer.create(serializer.validated_data)
        return Response(
            FavoriteSerializer(favorite).data,
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        serializer = FavoriteSerializer(
            data={},
            context={'request': request, 'id': pk}
        )
        serializer.delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_cart_item = ShopingCart.objects.filter(
            user=request.user,
            recipe=recipe
        )
        if shopping_cart_item.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = ShopingCartSerializer(
            data={},
            context={'request': request, 'id': pk}
        )
        serializer.is_valid()
        cart = serializer.create(serializer.validated_data)
        return Response(
            FavoriteSerializer(cart).data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        serializer = ShopingCartSerializer(
            data={},
            context={'request': request, 'id': pk}
        )
        serializer.delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        response = HttpResponse(content_type='text/plain')
        shoping_cart = ShopingCart.objects.filter(
            user=request.user
        ).values_list('recipe', flat=True)
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=shoping_cart
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')
        for ingredient in ingredients:
            response.write(f"{ingredient['ingredient__name']}\t"
                           f"{ingredient['amount']}\t"
                           f"{ingredient['ingredient__measurement_unit']}"
                           .encode("utf-8"))
        response['Content-Disposition'] = 'attachment; filename="cart.txt"'
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[permissions.AllowAny]
    )
    def get_link(self, request, pk):
        recipe = self.get_object()
        if not recipe.link:
            recipe.link = request.build_absolute_uri(f'/s/{recipe.id}')
            recipe.save()
        return Response({'short-link': recipe.link}, status=status.HTTP_200_OK)


def decode_link(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    return redirect(f'/recipes/{recipe.id}')
