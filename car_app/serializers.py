from .models import *
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'is_customer', 'is_admin']


class UserSerializerToken(UserSerializer):
    access = serializers.SerializerMethodField(read_only=True)
    refresh = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'refresh', 'access']

    @staticmethod
    def get_access(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)

    @staticmethod
    def get_refresh(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token)


class CarSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Car
        fields = ['id', 'brand', 'model', 'production_year', 'mileage', 'vin', 'daily_rate', 'availability',
                  'description']


class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'date_of_birth', 'licence_expiry_date', 'licence_since', 'address', 'city',
                  'country', 'citizenship']


class AccessorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Accessory
        fields = '__all__'


class RentalSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    car = CarSerializer(read_only=True)

    class Meta:
        model = Rental
        fields = ['id', 'customer', 'car', 'start_date', 'end_date', 'total_cost']


class PaymentSerializer(serializers.ModelSerializer):
    rental = RentalSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'rental', 'amount', 'payment_date']
