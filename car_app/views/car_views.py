from car_app.filters import CarFilter
from car_app.serializers import *
from rest_framework.permissions import AllowAny
from car_app.permissions import IsOwner
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from docs.car_views_docs import CAR_DETAIL_SCHEMA, LIST_CARS_SCHEMA


@LIST_CARS_SCHEMA
class CarListView(generics.ListAPIView):
    """
    Gets a list of all cars.
    """
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CarFilter
    ordering_fields = ['daily_rate', 'mileage', 'production_year']
    ordering = ['-production_year']


@CAR_DETAIL_SCHEMA
class CarDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [IsOwner()]
