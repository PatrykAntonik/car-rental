from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/docs/', SpectacularSwaggerView.as_view(), name='docs'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(), name='redoc'),

    path('api/users/', include('car_app.urls.user_urls')),
    path('api/cars/', include('car_app.urls.car_urls')),
    path('api/customers/', include('car_app.urls.customer_urls')),
    path('api/rentals/', include('car_app.urls.rental_urls')),
]
