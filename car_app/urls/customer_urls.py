from django.urls import path
from car_app.views.customer_views import *

urlpatterns = [
    path('register/', RegisterCustomer.as_view(), name='customer-register'),
    path('profile/', CustomerProfileView.as_view(), name='customer-profile'),
    path('my-rentals/', CustomerRentalListView.as_view(), name='customer-rentals'),
    path('<str:pk>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('', CustomerListView.as_view(), name='customers')
]
