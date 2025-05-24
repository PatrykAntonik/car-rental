from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse, OpenApiExample
from rest_framework import serializers
from car_app.messages import *
from car_app.serializers import RentalSerializer, PaymentSerializer

LIST_CUSTOMER_RENTALS = extend_schema(
    tags=["Rentals"],
    summary="List of rentals for an authenticated customer.",
    responses={
        200: RentalSerializer(many=True),
        404: OpenApiResponse(
            response=inline_serializer(
                name="CustomerNotFound",
                fields={"message": serializers.CharField()},
            ),
            description="The authenticated user is not linked to a Customer record.",
            examples=[
                OpenApiExample(
                    name="Customer missing",
                    value={"message": CUSTOMER_NOT_FOUND},
                    status_codes=["404"],
                    response_only=True,
                )
            ],
        ),
    },
)

RentalWithPayment = inline_serializer(
    name="RentalWithPayment",
    fields={
        **{name: field for name, field in RentalSerializer().fields.items()},
        "payment": PaymentSerializer(),
    },
)

RentalCreateRequest = inline_serializer(
    name="RentalCreateRequest",
    fields={
        "car": serializers.IntegerField(),
        "start_date": serializers.DateField(),
        "end_date": serializers.DateField(),
    },
)

CREATE_RENTAL_SCHEMA = extend_schema(
    tags=["Rentals"],
    summary="Create a new rental",
    description="Creates a new rental for the authenticated customer.",
    request=RentalCreateRequest,
    responses={
        201: RentalWithPayment,
        400: OpenApiResponse(
            response=inline_serializer(
                name="RentalCreationError",
                fields={"message": serializers.CharField()},
            ),
            description="The request data is invalid or the car is not available.",
            examples=[
                OpenApiExample(
                    name="Invalid data",
                    value={"message": "Invalid start or end date."},
                    status_codes=["400"],
                    response_only=True,
                )
            ],
        ),
    },
)

RENTAL_DETAIL_SCHEMA = extend_schema(
    tags=["Rentals"],
    summary="Rental detail",
    description="Returns the details of a specific rental.",
    responses={
        200: RentalWithPayment,
        404: OpenApiResponse(
            response=inline_serializer(
                name="RentalNotFound",
                fields={"message": serializers.CharField()},
            ),
            description="The rental with the given ID does not exist.",
            examples=[
                OpenApiExample(
                    name="Rental not found",
                    value={"message": RENTAL_NOT_FOUND},
                    status_codes=["404"],
                    response_only=True,
                )
            ],
        ),
    },
)

RENTAL_LIST_SCHEMA = extend_schema(
    tags=["Rentals"],
    summary="List rentals for the authenticated owner",
    description="Returns a list of all rentals in the system.",
    responses={
        200: RentalSerializer(many=True)
    },
)
