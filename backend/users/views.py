import os

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.paginators import FoodgramPagination
from api.serializers import FoodgramUserSerializer, SubscribeSerializer
from users.models import Subscription


User = get_user_model()


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
