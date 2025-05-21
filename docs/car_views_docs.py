from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from car_app.serializers import CarSerializer

LIST_CARS_SCHEMA = extend_schema(
    summary="List cars",
    description="List all cars with filter, search and ordering.",
    tags=["Car Management"],
)

CAR_DETAIL_SCHEMA = extend_schema_view(
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
