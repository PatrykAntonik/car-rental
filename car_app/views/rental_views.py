from datetime import date
from django.db import transaction
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from car_app.messages import *
from car_app.permissions import IsOwner, IsCustomer
from car_app.serializers import *
from docs.rental_views_docs import LIST_CUSTOMER_RENTALS, CREATE_RENTAL_SCHEMA, RENTAL_DETAIL_SCHEMA, RENTAL_LIST_SCHEMA


@LIST_CUSTOMER_RENTALS
class CustomerRentalListView(APIView):
    """
    List all rentals for the authenticated customer.
    """
    permission_classes = [IsAuthenticated, IsCustomer]

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


@RENTAL_DETAIL_SCHEMA
class RentalDetailView(generics.RetrieveUpdateAPIView):
    """
    Rental detail view for updating and retrieving rental information.
    """
    permission_classes = [IsOwner]
    serializer_class = RentalSerializer
    queryset = Rental.objects.select_related('car', 'customer__user')

    def retrieve(self, request, *args, **kwargs):
        rental = self.get_object()
        data = self.get_serializer(rental).data

        payment = Payment.objects.filter(rental=rental).first()
        if payment:
            data["payment"] = PaymentSerializer(payment).data
        else:
            data["payment"] = {"message": PAYMENT_NOT_FOUND}

        return Response(data, status=status.HTTP_200_OK)


@CREATE_RENTAL_SCHEMA
class RentalCreateView(generics.GenericAPIView):
    """
    Rental creation view for customers to book a car.
    """
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = RentalSerializer

    def post(self, request):
        car_id = request.data.get("car")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        try:
            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
        except (TypeError, ValueError):
            return Response(
                {"message": "start_date and end_date must be YYYY-MM-DD"},
                status=400,
            )

        try:
            customer: Customer = request.user.customer
        except Customer.DoesNotExist:
            return Response({"message": "User is not a customer"}, status=403)

        try:
            car = Car.objects.get(pk=car_id, availability=True)
        except Car.DoesNotExist:
            return Response({"message": "Car not available"}, status=400)

        if end_date <= start_date:
            return Response({"message": "end_date must be after start_date"}, status=400)

        overlap = Rental.objects.filter(
            car=car,
            start_date__lt=end_date,
            end_date__gt=start_date,
        ).exists()
        if overlap:
            return Response({"message": "Car already booked for given dates"}, status=400)

        days = (end_date - start_date).days + 1
        total_cost = car.daily_rate * days

        with transaction.atomic():
            rental = Rental.objects.create(
                customer=customer,
                car=car,
                start_date=start_date,
                end_date=end_date,
                total_cost=total_cost,
                status="pending",
            )
            payment = Payment.objects.create(
                rental=rental,
                amount=total_cost,
                status="completed",
            )

        data = self.get_serializer(rental).data
        data["payment"] = PaymentSerializer(payment).data
        return Response(data, status=status.HTTP_201_CREATED)


@RENTAL_LIST_SCHEMA
class RentalListView(generics.ListAPIView):
    """
    List all rentals for owner user.
    """
    permission_classes = [IsOwner]
    serializer_class = RentalSerializer

    def get_queryset(self):
        return Rental.objects.select_related('car', 'customer__user').all()
