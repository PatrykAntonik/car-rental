from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer, OpenApiResponse, \
    extend_schema_view
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from car_app.filters import CarFilter
from car_app.serializers import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from car_app.permissions import IsOwner
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    summary="List cars",
    description="List all cars with filter, search and ordering.",
    tags=["Car Management"],
)
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


@extend_schema_view(
    get=extend_schema(
        summary="Get car details",
        responses={200: CarSerializer},
        tags=["Car Management"],
    ),
    put=extend_schema(
        summary="Update car details",
        request=CarSerializer,
        responses={
            200: CarSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Not owner"),
        },
        tags=["Car Management"],
    ),
    delete=extend_schema(
        summary="Delete car",
        responses={
            204: OpenApiResponse(description="Deleted"),
            403: OpenApiResponse(description="Not owner"),
        },
        tags=["Car Management"],
    ),
)
class CarDetailView(APIView):
    """
    Car detail view to retrieve, update, or delete a specific car.
    """
    serializer_class = CarSerializer

    @permission_classes([AllowAny])
    def get(self, request, pk):
        car = get_object_or_404(Car, pk=pk)
        serializer = self.serializer_class(car, many=False)
        return Response(serializer.data)

    @permission_classes([IsOwner])
    def put(self, request, pk):
        car = get_object_or_404(Car, pk=pk)
        serializer = self.serializer_class(car, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    @permission_classes([IsOwner])
    def delete(self, request, pk):
        car = get_object_or_404(Car, pk=pk)
        car.delete()
        return Response(status=HTTP_204_NO_CONTENT)
