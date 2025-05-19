from rest_framework.response import Response
from rest_framework.views import APIView

from car_app.permissions import IsOwner
from car_app.serializers import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer, OpenApiResponse
from django.shortcuts import get_object_or_404


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


@extend_schema(
    summary="Login – obtain JWT",
    request=inline_serializer(
        name="TokenRequest",
        fields={
            "email": serializers.EmailField(),
            "password": serializers.CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="TokenResponse",
            fields={
                "access": serializers.CharField(),
                "refresh": serializers.CharField(),
            },
        ),
        401: OpenApiResponse(description="Invalid credentials"),
    },
    tags=["Authentication"],
)
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Handles token obtainment for authentication.
    """
    serializer_class = MyTokenObtainPairSerializer


@extend_schema(
    summary="List users",
    description="Retrieves a list of all users. Only accessible by admin users. Supports filtering, searching, and ordering.",
    responses={200: UserSerializer(many=True)},
    tags=["User Management"],
)
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


class UserProfileView(APIView):
    """
    User profile view for authenticated users.
    GET/ PUT/ DELETE methods.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get user profile",
        description="""
        Retrieve the profile information of the authenticated user.
        """,
        responses={
            200: UserSerializer,
            404: OpenApiResponse(
                description="User not found",
                response=inline_serializer(
                    name='UserNotFound',
                    fields={
                        'message': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'message': 'User not found'},
                    ),
                ]
            ),
        },
        tags=["User Management"]
    )
    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user, many=False)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=404)

    @extend_schema(
        summary="Update user profile",
        description="""
        Update the profile information of the authenticated user.
        """,
        request=inline_serializer(
            name='UpdateUserProfile',
            fields={
                'first_name': serializers.CharField(required=False, help_text="User's first name"),
                'last_name': serializers.CharField(required=False, help_text="User's last name"),
                'email': serializers.EmailField(required=False, help_text="User's email address"),
                'phone_number': serializers.CharField(required=False, help_text="User's phone number"),
            }
        ),
        responses={
            201: UserSerializer,
            400: OpenApiResponse(
                description="Bad request",
                response=inline_serializer(
                    name='UpdateError',
                    fields={
                        'message': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Email Taken',
                        value={'message': 'This email address is already in use by another account'},
                    ),
                    OpenApiExample(
                        'Phone Taken',
                        value={'message': 'This phone number is already in use by another account'},
                    ),
                ]
            ),
        },
        tags=["User Management"]
    )
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
                return Response({'message': 'This email address is already in use by another account'}, status=400)
            elif 'UNIQUE constraint failed: car_app_user.phone_number' in str(e):
                return Response({'message': 'This phone number is already in use by another account'}, status=400)
            else:
                return Response({'message': str(e)}, status=400)

        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=201)

    @extend_schema(
        summary="Delete user account",
        description="""
        Delete the authenticated user's account. Requires password confirmation.
        """,
        request=inline_serializer(
            name='DeleteUserAccount',
            fields={
                'password': serializers.CharField(help_text="Current password for confirmation"),
            }
        ),
        responses={
            204: OpenApiResponse(description="Account deleted successfully"),
            400: OpenApiResponse(
                description="Invalid password",
                response=inline_serializer(
                    name='DeleteError',
                    fields={
                        'message': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Invalid Password',
                        value={'message': 'Invalid password'},
                    ),
                ]
            ),
        },
        tags=["User Management"]
    )
    def delete(self, request):
        user = request.user
        old_password = request.data.get('password')
        if not user.check_password(old_password):
            return Response({'message': 'Invalid password'}, status=400)
        user.delete()
        return Response(status=204)


@extend_schema(tags=['User Management'])
class ChangePasswordView(APIView):
    """
    Password change view for authenticated users.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Change password",
        request=inline_serializer(
            name="ChangePasswordRequest",
            fields={
                "old_password": serializers.CharField(),
                "new_password": serializers.CharField(),
            },
        ),
        responses={
            200: OpenApiResponse(
                description="Password changed",
                examples=[OpenApiExample("Success", value={"message": "Password changed successfully"})],
            ),
            400: OpenApiResponse(
                description="Invalid old password",
                examples=[OpenApiExample("Invalid", value={"message": "Invalid password"})],
            ),
        },
    )
    def put(self, request):
        user = request.user
        data = request.data
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not user.check_password(old_password):
            return Response({'message': 'Invalid password'}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'}, status=201)


@extend_schema(tags=['User Management'])
class UserDetailView(APIView):
    """
    Retrieves user details for admin.
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Get user details",
        responses={200: UserSerializer},
    )
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)


@extend_schema(tags=['Authentication'])
class RegisterUser(APIView):
    """
    User
    registration
    view.
    """

    @extend_schema(
        summary="Register a new user",
        request=inline_serializer(
            name="UserRegistration",
            fields={
                "first_name": serializers.CharField(required=False),
                "last_name": serializers.CharField(required=False),
                "email": serializers.EmailField(),
                "phone_number": serializers.CharField(),
                "password": serializers.CharField(write_only=True),
                "is_customer": serializers.BooleanField(default=False),
                "is_owner": serializers.BooleanField(default=False),
            },
        ),
        responses={
            201: UserSerializer,
            400: OpenApiResponse(
                description="Validation / integrity error",
                examples=[
                    OpenApiExample("Both roles set", value={"message": "User cannot be both customer and owner"}),
                    OpenApiExample("Email duplicate", value={"message": "Email already registered"}),
                    OpenApiExample("Phone duplicate", value={"message": "Phone number already registered"}),
                ],
            ),
        },
    )
    def post(self, request):
        data = request.data
        is_customer = data.get('is_customer', False)
        is_owner = data.get('is_owner', False)
        if is_customer and is_owner:
            return Response(
                {'message': 'User cannot be both customer and owner'},
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
                    {'message': 'Email already registered'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'phone_number' in str(e):
                return Response(
                    {'message': 'Phone number already registered'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'message': 'Registration failed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


