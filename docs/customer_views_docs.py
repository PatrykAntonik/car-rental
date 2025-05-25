from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse, OpenApiExample, extend_schema_view
from rest_framework import serializers
from car_app.messages import *

from car_app.serializers import CustomerSerializer

REGISTER_CUSTOMER_SCHEMA = extend_schema(
    tags=["Authentication"],
    summary="Register a new customer (User + Customer profile)",
    request=inline_serializer(
        name="CustomerRegistration",
        fields={
            "first_name": serializers.CharField(required=False),
            "last_name": serializers.CharField(required=False),
            "email": serializers.EmailField(),
            "phone_number": serializers.CharField(),
            "password": serializers.CharField(write_only=True),
            "date_of_birth": serializers.DateField(format="iso-8601"),
            "licence_since": serializers.DateField(format="iso-8601"),
            "licence_expiry_date": serializers.DateField(format="iso-8601"),
            "address": serializers.CharField(),
            "city": serializers.CharField(),
            "country": serializers.CharField(),
            "citizenship": serializers.CharField(),
        },
    ),
    responses={
        201: CustomerSerializer,
        400: OpenApiResponse(
            description=REGISTRATION_FAILURE,
            examples=[
                OpenApiExample("Email duplicate", value={"message": EMAIL_ALREADY_REGISTERED}),
                OpenApiExample("Phone duplicate", value={"message": PHONE_ALREADY_REGISTERED}),
            ],
        ),
    },
)

LIST_CUSTOMERS_SCHEMA = extend_schema(
    summary="List customers",
    description="Retrieves a list of all customers. Only accessible by users with Owner role. Supports filtering, searching, and ordering.",
    responses={200: CustomerSerializer(many=True)},
    tags=["Customers"],
)

CUSTOMER_PROFILE_SCHEMA = extend_schema_view(
    get=extend_schema(
        summary="Get customer profile",
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(
                description="Customer profile not found",
                response=inline_serializer(
                    name="CustomerNotFound",
                    fields={"message": serializers.CharField()},
                ),
                examples=[
                    OpenApiExample("Not Found", value={"message": "Customer profile not found"}),
                ],
            ),
        },
        tags=["Customers"]
    ),
    put=extend_schema(
        summary="Update customer profile",
        request=inline_serializer(
            name="UpdateCustomerProfile",
            fields={
                "date_of_birth": serializers.DateField(required=False),
                "licence_since": serializers.DateField(required=False),
                "licence_expiry_date": serializers.DateField(required=False),
                "address": serializers.CharField(required=False),
                "city": serializers.CharField(required=False),
                "country": serializers.CharField(required=False),
                "citizenship": serializers.CharField(required=False),
            },
        ),
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(description="Customer profile not found"),
        },
        tags=["Customers"]
    ),
    patch=extend_schema(
        summary="Partially update customer profile",
        request=inline_serializer(
            name="PartialUpdateCustomerProfile",
            fields={
                "date_of_birth": serializers.DateField(required=False),
                "licence_since": serializers.DateField(required=False),
                "licence_expiry_date": serializers.DateField(required=False),
                "address": serializers.CharField(required=False),
                "city": serializers.CharField(required=False),
                "country": serializers.CharField(required=False),
                "citizenship": serializers.CharField(required=False),
            },
        ),
        responses={
            200: CustomerSerializer,
            404: OpenApiResponse(description="Customer profile not found"),
        },
        tags=["Customers"]
    ),
    post=extend_schema(
        summary="Create customer profile",
        request=inline_serializer(
            name="CreateCustomerProfile",
            fields={
                "date_of_birth": serializers.DateField(),
                "licence_since": serializers.DateField(),
                "licence_expiry_date": serializers.DateField(),
                "address": serializers.CharField(),
                "city": serializers.CharField(),
                "country": serializers.CharField(),
                "citizenship": serializers.CharField(),
            },
        ),
        responses={
            201: CustomerSerializer,
            400: OpenApiResponse(description=CUSTOMER_PROFILE_EXISTS),
        },
        tags=["Customers"]
    ),
)

CUSTOMER_DETAIL_SCHEMA = extend_schema(
    tags=['Customers'],
    summary="Get customer details",
    responses={200: CustomerSerializer}
)
