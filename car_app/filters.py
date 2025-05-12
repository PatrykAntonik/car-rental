from django_filters import rest_framework as filters
from car_app.models import *


class CarFilter(filters.FilterSet):
    brand = filters.MultipleChoiceFilter(
        choices=Car.objects.values_list('brand', 'brand').distinct(),
        lookup_expr='in'
    )
    daily_rate_min = filters.NumberFilter(field_name="daily_rate", lookup_expr='gte')
    daily_rate_max = filters.NumberFilter(field_name="daily_rate", lookup_expr='lte')
    production_year_min = filters.NumberFilter(field_name="production_year", lookup_expr='gte')
    production_year_max = filters.NumberFilter(field_name="production_year", lookup_expr='lte')
    mileage_min = filters.NumberFilter(field_name="mileage", lookup_expr='gte')
    mileage_max = filters.NumberFilter(field_name="mileage", lookup_expr='lte')

    class Meta:
        model = Car
        fields = {
            'model': ['exact', 'icontains'],
            'availability': ['exact'],
        }
