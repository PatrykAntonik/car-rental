from django.urls import path
from car_app.views.rental_views import *

urlpatterns = [
    path('my-rentals/', CustomerRentalListView.as_view(), name='customer-rentals'),
    path('create/', RentalCreateView.as_view(), name='rental-create'),
    path('<str:pk>/', RentalDetailView.as_view(), name='rental-detail'),
    path('', RentalListView.as_view(), name='rental-list'),
]
