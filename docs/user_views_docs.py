from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse, extend_schema_view, OpenApiExample
from rest_framework import serializers
from car_app.serializers import UserSerializer
from car_app.messages import *

LOGIN_SCHEMA = extend_schema(
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
        401: OpenApiResponse(description=INVALID_CREDENTIALS),
    },
    tags=["Authentication"],
)

USER_LIST_SCHEMA = extend_schema(
    summary="List users",
    description="Retrieves a list of all users. Only accessible by admin users. Supports filtering, searching, and ordering.",
    responses={200: UserSerializer(many=True)},
    tags=["User Management"],
)

USER_PROFILE_SCHEMA = extend_schema_view(
    get=extend_schema(
        summary="Get user profile",
        description="Retrieve the profile information of the authenticated user.",
        responses={
            200: UserSerializer,
            404: OpenApiResponse(
                description=USER_NOT_FOUND,
                response=inline_serializer(
                    name="UserNotFound",
                    fields={"message": serializers.CharField()},
                ),
                examples=[
                    OpenApiExample("Not Found", value={"message": USER_NOT_FOUND}),
                ],
            ),
        },
        tags=["User Management"],
    ),

    put=extend_schema(
        summary="Update user profile",
        description="Update the profile information of the authenticated user.",
        request=inline_serializer(
            name="UpdateUserProfile",
            fields={
                "first_name": serializers.CharField(required=False, help_text="User's first name"),
                "last_name": serializers.CharField(required=False, help_text="User's last name"),
                "email": serializers.EmailField(required=False, help_text="User's email address"),
                "phone_number": serializers.CharField(required=False, help_text="User's phone number"),
            },
        ),
        responses={
            201: UserSerializer,
            400: OpenApiResponse(
                description="Bad request",
                response=inline_serializer(
                    name="UpdateError",
                    fields={"message": serializers.CharField()},
                ),
                examples=[
                    OpenApiExample("Email Taken", value={"message": EMAIL_ALREADY_REGISTERED}),
                    OpenApiExample("Phone Taken", value={"message": PHONE_ALREADY_REGISTERED}),
                ],
            ),
        },
        tags=["User Management"],
    ),

    delete=extend_schema(
        summary="Delete user account",
        description="Delete the authenticated user's account. Requires password confirmation.",
        request=inline_serializer(
            name="DeleteUserAccount",
            fields={"password": serializers.CharField(help_text="Current password for confirmation")},
        ),
        responses={
            204: OpenApiResponse(description=ACCOUNT_DELETED_SUCCESS),
            400: OpenApiResponse(
                description=INVALID_PASSWORD,
                response=inline_serializer(
                    name="DeleteError",
                    fields={"message": serializers.CharField()},
                ),
                examples=[
                    OpenApiExample("Invalid Password", value={"message": INVALID_PASSWORD}),
                ],
            ),
        },
        tags=["User Management"],
    ),
    patch=extend_schema(
        summary="Update user profile partially",
        description="Partially update the profile information of the authenticated user.",
        request=inline_serializer(
            name="PartialUpdateUserProfile",
            fields={
                "first_name": serializers.CharField(required=False, help_text="User's first name"),
                "last_name": serializers.CharField(required=False, help_text="User's last name"),
                "email": serializers.EmailField(required=False, help_text="User's email address"),
                "phone_number": serializers.CharField(required=False, help_text="User's phone number"),
            },
        ),
        responses={
            200: UserSerializer,
            400: OpenApiResponse(
                description="Bad request",
                response=inline_serializer(
                    name="PartialUpdateError",
                    fields={"message": serializers.CharField()},
                ),
                examples=[
                    OpenApiExample("Email Taken", value={"message": EMAIL_ALREADY_REGISTERED}),
                    OpenApiExample("Phone Taken", value={"message": PHONE_ALREADY_REGISTERED}),
                ],
            ),
        },
        tags=["User Management"],
    ),
)

UPDATE_PASSWORD_SCHEMA = extend_schema(
    tags=["User Management"],
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
            description=PASSWORD_CHANGE_SUCCESS,
            examples=[OpenApiExample("Success", value={"message": PASSWORD_CHANGE_SUCCESS})],
        ),
        400: OpenApiResponse(
            description=INVALID_PASSWORD,
            examples=[OpenApiExample("Invalid", value={"message": INVALID_PASSWORD})],
        ),
    },
)

USER_DETAIL_SCHEMA = extend_schema(
    tags=['User Management'],
    summary="Get user details",
    responses={200: UserSerializer},
)

REGISTER_USER_SCHEMA = extend_schema(
    tags=["Authentication"],
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
            description=REGISTRATION_FAILURE,
            examples=[
                OpenApiExample("Both roles set", value={"message": DUPLICATE_ROLE}),
                OpenApiExample("Email duplicate", value={"message": EMAIL_ALREADY_REGISTERED}),
                OpenApiExample("Phone duplicate", value={"message": PHONE_ALREADY_REGISTERED}),
            ],
        ),
    },
)
