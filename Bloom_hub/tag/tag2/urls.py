from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tag/', include('tag.urls')),  # myapp의 urls.py 포함
]
