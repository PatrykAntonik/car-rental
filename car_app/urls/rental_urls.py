from django.urls import path
from car_app.views.rental_views import *

urlpatterns = [
    path('my-rentals/', CustomerRentalListView.as_view(), name='customer-rentals'),
    path('<str:pk>/', RentalDetailView.as_view(), name='rental-detail'),
    path('create/', RentalCreateView.as_view(), name='rental-create'),
    path('', RentalListView.as_view(), name='rental-list'),
]
