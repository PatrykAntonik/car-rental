from rest_framework.response import Response
from rest_framework.views import APIView

from car_app.serializers import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from car_app.permissions import IsOwner
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Get JWT token with user data.
    """
    username_field = 'email'

    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerToken(self.user).data
        for i, j in serializer.items():
            data[i] = j
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Handles token obtainment for authentication.
    """
    serializer_class = MyTokenObtainPairSerializer


class UserListView(generics.ListAPIView):
    """
    Retrieves a list of users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'is_customer', 'is_owner']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    ordering_fields = ['city', 'is_customer', 'is_owner']


class UserProfileView(APIView):
    """

    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserSerializer(user, many=False)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=404)

    def put(self, request):
        user = request.user
        data = request.data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.phone_number = data.get('phone_number', user.phone_number)

        try:
            user.save()
        except Exception as e:
            if 'UNIQUE constraint failed: car_app_user.email' in str(e):
                return Response({'message': 'This email address is already in use by another account'}, status=400)
            elif 'UNIQUE constraint failed: car_app_user.phone_number' in str(e):
                return Response({'message': 'This phone number is already in use by another account'}, status=400)
            else:
                return Response({'message': str(e)}, status=400)

        serializer = UserSerializer(user, many=False)
        return Response(serializer.data, status=201)

    def delete(self, request):
        user = request.user
        old_password = request.data.get('password')
        if not user.check_password(old_password):
            return Response({'message': 'Invalid password'}, status=400)
        user.delete()
        return Response(status=204)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        Change the password of the authenticated user.
        """
        user = request.user
        data = request.data
        old_password = data.get('old_password')
        new_password = data.get('new_password')

        if not user.check_password(old_password):
            return Response({'message': 'Invalid password'}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'}, status=201)


class AdminUserDetailView(APIView):
    """
    Retrieves user details for admin.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        user = get_object_or_404(User, pk)
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
