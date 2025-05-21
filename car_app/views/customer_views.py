from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from car_app.permissions import IsOwner
from car_app.serializers import *
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import generics, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from docs.customer_views_docs import *


@REGISTER_CUSTOMER_SCHEMA
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
                    {'message': EMAIL_ALREADY_REGISTERED},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'phone_number' in str(e):
                return Response(
                    {'message': PHONE_ALREADY_REGISTERED},
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
        serializer = CustomerSerializer(customer, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@LIST_CUSTOMERS_SCHEMA
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


@CUSTOMER_PROFILE_SCHEMA
class CustomerProfileView(APIView):
    """
    Customer profile view.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            return Response({"message": CUSTOMER_NOT_FOUND}, status=404)

        return Response(CustomerSerializer(customer).data)

    def put(self, request):
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            return Response({"message": CUSTOMER_NOT_FOUND}, status=404)

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
        return Response(CustomerSerializer(customer).data, status=HTTP_200_OK)


@LIST_CUSTOMER_RENTALS
class CustomerRentalListView(APIView):
    """
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            return Response(
                {"message": CUSTOMER_NOT_FOUND},
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
                rent_data["payment"] = {"message": PAYMENT_NOT_FOUND}

            result.append(rent_data)

        return Response(result, status=status.HTTP_200_OK)


@CUSTOMER_DETAIL_SCHEMA
class CustomerDetailView(APIView):
    """
    Retrieves customer details for admin.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        serializer = CustomerSerializer(customer, many=False)
        return Response(serializer.data)
