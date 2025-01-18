from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription
from users.paginators import FoodgramPagination
from users.serializers import (
    FoodgramUserSerializer,
    SetPasswordSerializer,
    SubscribeSerializer
)

User = get_user_model()


class FoodgramUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = FoodgramPagination
    permission_classes = []

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        return Response(
            FoodgramUserSerializer(request.user).data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['put'],
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        if not request.data.get('avatar'):
            return Response(status=status.HTTP_400_BAD_REQUEST)
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
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        recipes_limit = request.query_params.get('recipes_limit')
        subscriptions_items = request.user.subscripted.all()
        subscriptions = [
            subscription.following for subscription in subscriptions_items
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
        following = get_object_or_404(User, id=id)
        recipes_limit = request.query_params.get('recipes_limit')
        subscription = Subscription.objects.filter(
            follower=request.user,
            following=following
        )
        if subscription.exists() or following.id == request.user.id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = SubscribeSerializer(
            data={},
            context={'request': request,
                     'recipes_limit': recipes_limit,
                     'id': id}
        )
        serializer.is_valid()
        subscription = serializer.create(serializer.validated_data)
        return Response(SubscribeSerializer(
            subscription,
            context={'request': request, 'recipes_limit': recipes_limit}
        ).data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id):
        following = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            follower=request.user,
            following=following
        )
        if not subscription.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = SubscribeSerializer(
            data={},
            context={'request': request, 'id': id}
        )
        serializer.delete(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
