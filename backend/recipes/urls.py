from django.urls import path

from recipes.views import decode_link

urlpatterns = [
    path('<int:id>', decode_link, name='short_link')
]
