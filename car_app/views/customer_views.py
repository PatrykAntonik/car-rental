from rest_framework.response import Response
from rest_framework.views import APIView
from car_app.permissions import IsOwner
from car_app.serializers import *
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer, OpenApiResponse
from django.shortcuts import get_object_or_404


@extend_schema(
    tags=['Authentication'],
    summary="Register a new customer (User + Customer profile)",
    request=CustomerRegistrationDocSerializer,
    responses={201: CustomerSerializer},
)
class RegisterCustomer(APIView):
    """
    Customer registration view.
    """

    def post(self, request):
        data = request.data

        user_data = {
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "email": data.get("email", ""),
            "phone_number": data.get("phone_number", ""),
            "password": data.get("password", ""),
            "is_customer": True,  # na stałe
            "is_owner": False,
        }
        customer_data = {
            "date_of_birth": data.get("date_of_birth"),
            "licence_since": data.get("licence_since"),
            "licence_expiry_date": data.get("licence_expiry_date"),
            "address": data.get("address"),
            "city": data.get("city"),
            "country": data.get("country"),
            "citizenship": data.get("citizenship"),
        }

        try:
            with transaction.atomic():
                user = User.objects.create_user(**user_data)
                customer = Customer.objects.create(user=user, **customer_data)

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
        serializer = CustomerSerializer(customer, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="List customers",
    description="Retrieves a list of all customers. Only accessible by users with Owner role. Supports filtering, searching, and ordering.",
    responses={200: CustomerSerializer(many=True)},
    tags=["Customers"],
)
class CustomerListView(generics.ListAPIView):
    """
    Retrieves a list of customers.
    """

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'country', 'citizenship']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'user__phone_number']
    ordering_fields = ['licence_since', 'date_of_birth']


@extend_schema(tags=["Customers"])
class CustomerProfileView(APIView):
    """
    Customer profile view.
    """
    permission_classes = [IsAuthenticated]

    # ---------- GET ----------
    @extend_schema(
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
    )
    def get(self, request):
        """
        """
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            return Response({"message": "Customer profile not found"}, status=404)

        return Response(CustomerSerializer(customer).data)

    @extend_schema(
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
    )
    def put(self, request):
        """
        """
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            return Response({"message": "Customer profile not found"}, status=404)

        data = request.data
        for field in (
                "date_of_birth",
                "licence_since",
                "licence_expiry_date",
                "address",
                "city",
                "country",
                "citizenship",
        ):
            if field in data:
                setattr(customer, field, data[field])

        customer.save()
        return Response(CustomerSerializer(customer).data, status=200)


@extend_schema(
    tags=["Customers"],
    summary="List of rentals for an authenticated customer.",
    responses={200: None}
)
class CustomerRentalListView(APIView):
    """
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            return Response(
                {"message": "Customer profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        rentals = (
            Rental.objects
            .filter(customer=customer)
            .select_related("car")
        )

        result = []
        for rent in rentals:
            rent_data = RentalSerializer(rent).data
            pay = Payment.objects.filter(rental=rent).first()
            if pay:
                rent_data["payment"] = PaymentSerializer(pay).data
            else:
                rent_data["payment"] = {"message": "Payment not found"}

            result.append(rent_data)

        return Response(result, status=status.HTTP_200_OK)


@extend_schema(tags=['Customers'])
class CustomerDetailView(APIView):
    """
    Retrieves customer details for admin.
    """

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Get customer details",
        responses={200: CustomerSerializer},
    )
    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        serializer = CustomerSerializer(customer, many=False)
        return Response(serializer.data)
