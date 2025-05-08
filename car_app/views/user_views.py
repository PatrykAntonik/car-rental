from rest_framework.response import Response
from rest_framework.views import APIView
from car_app.serializers import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from car_app.permissions import IsOwner
from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import IntegrityError
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
    tags=["Authentication"],
    summary="Obtain auth tokens",
    description="""
    Obtain JWT token pair for authentication.

    Provides access and refresh tokens upon successful login.
    """,
    request=inline_serializer(
        name='TokenObtainPairRequest',
        fields={
            'email': serializers.EmailField(help_text="User's email address"),
            'password': serializers.CharField(help_text="User's password")
        }
    ),

    responses={
        200: OpenApiResponse(
            description="Token pair obtained successfully",
            response=inline_serializer(
                name='TokenObtainPairResponse',
                fields={
                    'access': serializers.CharField(help_text="JWT access token"),
                    'refresh': serializers.CharField(help_text="JWT refresh token")
                }
            )
        ),
        401: OpenApiResponse(
            description="Invalid credentials",
            response=inline_serializer(
                name='TokenObtainPairError',
                fields={
                    'detail': serializers.CharField(),
                }
            ),
            examples=[
                OpenApiExample(
                    'Invalid Credentials',
                    value={'detail': 'No active account found with the given credentials'}
                ),
            ]
        )
    },

)
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Handles token obtainment for authentication.
    """
    serializer_class = MyTokenObtainPairSerializer


@extend_schema(
    summary="List all users",
    description="""
        Retrieves a list of all users. Only accessible by admin users.
        Supports filtering, searching, and ordering.

        - Filter by user type (is_customer, is_owner)
        - Search by name, email, or phone number
        - Order by user type
        """,
    parameters=[
        OpenApiParameter(
            name='is_customer',
            description='Filter by customer status',
            required=False,
            type=bool
        ),
        OpenApiParameter(
            name='is_owner',
            description='Filter by owner status',
            required=False,
            type=bool
        ),
        OpenApiParameter(
            name='search',
            description='Search in first name, last name, email, and phone number',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='ordering',
            description='Order by is_customer or is_owner (prefix with - for descending)',
            required=False,
            type=str,
            examples=[
                OpenApiExample(name='Ascending by customer', value='is_customer'),
                OpenApiExample(name='Descending by owner', value='-is_owner')
            ]
        ),
    ],
    responses={
        200: UserSerializer(many=True),
        401: OpenApiResponse(description="Authentication credentials were not provided"),
        403: OpenApiResponse(description="Not an admin user")
    },
    tags=["User Management"]
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
        summary="Change user password",
        description="""
        Change the authenticated user's password.

        Requires:
        - Current password for verification
        - New password to set
        """,
        request=inline_serializer(
            name='ChangePasswordRequest',
            fields={
                'old_password': serializers.CharField(
                    help_text="Current password"
                ),
                'new_password': serializers.CharField(
                    help_text="New password"
                ),
            }
        ),

        responses={
            201: OpenApiResponse(
                description="Password changed successfully",
                response=inline_serializer(
                    name='PasswordChangeSuccess',
                    fields={
                        'message': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'message': 'Password changed successfully'},
                    ),
                ]
            ),
            400: OpenApiResponse(
                description="Invalid old password",
                response=inline_serializer(
                    name='PasswordChangeError',
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
            401: OpenApiResponse(
                description="Authentication credentials were not provided",
                response=inline_serializer(
                    name='Unauthorized',
                    fields={
                        'detail': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Unauthorized',
                        value={'detail': 'Authentication credentials were not provided.'},
                    ),
                ]
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
        description="""
        Retrieves detailed information about a specific user. Accessible only by admin users.
        - Requires user ID in the URL path."""
        ,
        parameters=[
            OpenApiParameter(
                name='id',
                location='path',
                description='User ID',
                required=True,
                type=int
            )
        ],
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="User details retrieved successfully"
            ),
            404: OpenApiResponse(
                description="User not found",
                response=inline_serializer(
                    name='UserNotFoundError',
                    fields={
                        'detail': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Not found.'},
                    ),
                ]
            ),
            403: OpenApiResponse(
                description="Permission denied - Admin access required",
                response=inline_serializer(
                    name='PermissionDenied',
                    fields={
                        'detail': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Forbidden',
                        value={'detail': 'You do not have permission to perform this action.'},
                    ),
                ]
            ),
        },
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
        description="""
    Creates
    a
    new
    user as either
    a
    customer or an
    owner.
    - Only
    one
    role
    can
    be
    selected
    at
    a
    time.
    """,
        request=inline_serializer(
            name='UserRegistration',
            fields={
                'first_name': serializers.CharField(required=False),
                'last_name': serializers.CharField(required=False),
                'email': serializers.EmailField(required=True),
                'phone_number': serializers.CharField(required=True),
                'password': serializers.CharField(required=True, write_only=True),
                'is_customer': serializers.BooleanField(default=False),
                'is_owner': serializers.BooleanField(default=False),
            }
        ),

        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="User created successfully"
            ),
            400: OpenApiResponse(
                description="Bad Request",
                response=inline_serializer(
                    name='RegistrationError',
                    fields={
                        'message': serializers.CharField(),
                    }
                ),
                examples=[
                    OpenApiExample(
                        'Both roles set',
                        value={'message': 'User cannot be both customer and owner'},
                    ),
                    OpenApiExample(
                        'Email duplicate',
                        value={'message': 'Email already registered'},
                    ),
                    OpenApiExample(
                        'Phone duplicate',
                        value={'message': 'Phone number already registered'},
                    ),
                ]
            ),

        },
        tags=["Authentication"],
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
