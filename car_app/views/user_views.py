from google.oauth2 import id_token
from rest_framework.response import Response
from rest_framework.views import APIView
from docs.user_views_docs import *
from car_app.serializers import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from car_app.messages import *
from google.auth.transport import requests as google_requests
from car_rental.settings import GOOGLE_CLIENT_ID


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
    filterset_fields = ['is_owner']
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['is_owner']


@USER_PROFILE_SCHEMA
class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    User profile view for authenticated users.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.none()

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_update(serializer)
        except IntegrityError as e:
            if "email" in str(e):
                return Response({"message": EMAIL_ALREADY_REGISTERED}, status=400)
            return Response({"message": str(e)}, status=400)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if not user.check_password(request.data.get("password")):
            return Response({"message": INVALID_PASSWORD}, status=400)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
class UserDetailView(generics.RetrieveAPIView):
    """
    Retrieves user details for admin.
    """

    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()


@REGISTER_USER_SCHEMA
class RegisterUser(APIView):
    """
    User
    registration
    view.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        is_owner = data.get('is_owner', False)
        try:
            user = User.objects.create_user(
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                email=data.get('email', ''),
                password=data.get('password', ''),
                is_owner=is_owner,
            )
        except IntegrityError as e:
            if 'email' in str(e):
                return Response(
                    {'message': EMAIL_ALREADY_REGISTERED},
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


@GOOGLE_AUTH_SCHEMA
class GoogleAuthView(APIView):
    """
    Handles Google OAuth2 authentication.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"detail": "id_token is required"}, status=400)

        try:
            info = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID,
            )
        except ValueError:
            return Response({"detail": "Invalid token"}, status=400)

        email = info.get("email")
        first_name = info.get("given_name", "first_name")
        last_name = info.get("family_name", "last_name")

        if not email:
            return Response({"detail": "Email scope missing"}, status=400)

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
            },
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)},
            status=status.HTTP_201_CREATED,
        )
