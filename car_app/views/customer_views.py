from rest_framework.exceptions import NotFound
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
from docs.customer_views_docs import *


@REGISTER_CUSTOMER_SCHEMA
class RegisterCustomer(APIView):
    """
    Customer registration view.
    """
    permission_classes = [AllowAny]

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
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    """
    """
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.customer
        except Customer.DoesNotExist:
            raise NotFound({"message": CUSTOMER_NOT_FOUND})

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


@CUSTOMER_DETAIL_SCHEMA
class CustomerDetailView(generics.RetrieveAPIView):
    """
    Retrieves customer details for admin.
    """
    queryset = Customer.objects.select_related("user")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]
