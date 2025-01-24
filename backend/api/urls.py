from django.urls import include, path
from django.views.generic.base import TemplateView
from rest_framework import routers

from api.views import (FoodgramUserViewSet, IngredientViewSet,
                       RecipeViewSet, TagViewSet)

app_name = 'api'

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', FoodgramUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('docs/', TemplateView.as_view(template_name='docs/redoc.html'),
         name='redoc'),
]
