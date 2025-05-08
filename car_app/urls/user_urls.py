from django.urls import path
from car_app.views.user_views import *

urlpatterns = [
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', MyTokenObtainPairView.as_view(), name='login'),
    path('profile/password/', ChangePasswordView.as_view(), name='user-update-password'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('<str:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('', UserListView.as_view(), name='users')
]
