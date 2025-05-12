from django.urls import path
from car_app.views.car_views import *

urlpatterns = [
    path('car/<int:pk>/', CarDetailView.as_view(), name='car-detail'),
    path('', CarListView.as_view(), name='car-list'),
]
