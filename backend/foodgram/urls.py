from django.contrib import admin
from django.urls import include, path

from recipes.views import decode_link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<int:id>', decode_link, name='short_link')
]
