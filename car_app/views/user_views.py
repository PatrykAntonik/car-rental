from rest_framework.response import Response
from rest_framework.views import APIView
from docs.user_views_docs import LOGIN_SCHEMA, USER_LIST_SCHEMA, USER_PROFILE_SCHEMA, UPDATE_PASSWORD_SCHEMA, \
    USER_DETAIL_SCHEMA, REGISTER_USER_SCHEMA
from car_app.serializers import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from car_app.messages import *


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Get JWT token with user data.
    """
    username_field = 'email'

    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerToken(self.user).data
        for i, j in serializer.items():
            data[i] = j
        return data


@LOGIN_SCHEMA
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Handles token obtainment for authentication.
    """
    serializer_class = MyTokenObtainPairSerializer


@USER_LIST_SCHEMA
class UserListView(generics.ListAPIView):
    """
    Retrieves a list of users.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_customer', 'is_owner']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    ordering_fields = ['is_customer', 'is_owner']


@USER_PROFILE_SCHEMA
class UserProfileView(APIView):
    """
    User profile view for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user, many=False)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'message': USER_NOT_FOUND}, status=404)

    def put(self, request):
        user = request.user
        data = request.data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.phone_number = data.get('phone_number', user.phone_number)

        try:
            user.save()
        except Exception as e:
            if 'UNIQUE constraint failed: car_app_user.email' in str(e):
                return Response({'message': EMAIL_ALREADY_REGISTERED}, status=400)
            elif 'UNIQUE constraint failed: car_app_user.phone_number' in str(e):
                return Response({'message': PHONE_ALREADY_REGISTERED}, status=400)
            else:
                return Response({'message': str(e)}, status=400)

        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=201)

    def delete(self, request):
        user = request.user
        old_password = request.data.get('password')
        if not user.check_password(old_password):
            return Response({'message': INVALID_PASSWORD}, status=400)
        user.delete()
        return Response(status=204)


@UPDATE_PASSWORD_SCHEMA
class ChangePasswordView(APIView):
    """
    Password change view for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        data = request.data
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not user.check_password(old_password):
            return Response({'message': INVALID_PASSWORD}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'message': PASSWORD_CHANGE_SUCCESS}, status=201)


@USER_DETAIL_SCHEMA
class UserDetailView(APIView):
    """
    Retrieves user details for admin.
    """

    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)


@REGISTER_USER_SCHEMA
class RegisterUser(APIView):
    """
    User
    registration
    view.
    """

    def post(self, request):
        data = request.data
        is_customer = data.get('is_customer', False)
        is_owner = data.get('is_owner', False)
        if is_customer and is_owner:
            return Response(
                {'message': DUPLICATE_ROLE},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.create_user(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                email=data.get('email', ''),
                phone_number=data.get('phone_number', ''),
                password=data.get('password', ''),
                is_customer=is_customer,
                is_owner=is_owner,
            )
        except IntegrityError as e:
            if 'email' in str(e):
                return Response(
                    {'message': EMAIL_ALREADY_REGISTERED},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'phone_number' in str(e):
                return Response(
                    {'message': 'Phone number already registered'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'message': REGISTRATION_FAILURE},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
