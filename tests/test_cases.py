import pytest
from datetime import date
from decimal import Decimal
from rest_framework.test import APIRequestFactory, force_authenticate
from car_app.models import User, Customer, Car, Rental, Payment
from car_app.views.rental_views import CustomerRentalListView, RentalCreateView, RentalDetailView
from car_app.views.user_views import ChangePasswordView


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def owner_user(db):
    """A user flagged as owner"""
    return User.objects.create_user(
        email="owner@example.com",
        password="password",
        is_owner=True,
    )


@pytest.fixture
def customer_user(db):
    """Regular authenticated user"""
    return User.objects.create_user(
        email="customer@example.com",
        password="password",
        is_owner=False,
    )


@pytest.fixture
def customer(db, customer_user):
    """Customer profile associated with the user"""
    return Customer.objects.create(
        user=customer_user,
        date_of_birth=date(1990, 1, 1),
        licence_since=date(2010, 1, 1),
        licence_expiry_date=date(2030, 1, 1),
        address="Złota 44",
        city="Warsaw",
        country="Poland",
        citizenship="polish",
        phone_number="+48123456789",
    )


@pytest.fixture
def car(db):
    """Car object for testing"""
    return Car.objects.create(
        brand="Toyota",
        model="Corolla",
        description="Compact sedan",
        production_year=2020,
        mileage=10_000,
        vin="1HGCM82633A004352",
        daily_rate=Decimal("100.00"),
        availability=True,
    )


@pytest.mark.django_db
def test_get_customer_rental_list_success(factory, customer_user, customer, car):
    """
    """
    rental = Rental.objects.create(
        customer=customer,
        car=car,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
        total_cost=Decimal("300.00"),
        status="pending",
    )
    Payment.objects.create(rental=rental, amount=Decimal("300.00"), status="completed")
    request = factory.get("/rentals/my-rentals")
    force_authenticate(request, user=customer_user)
    response = CustomerRentalListView.as_view()(request)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == rental.id


@pytest.mark.django_db
def test_create_rental_success(factory, customer_user, customer, car):
    """
    """
    data = {
        "car": car.id,
        "start_date": "2024-02-01",
        "end_date": "2024-02-02",
    }
    request = factory.post("/rentals/create/", data, format="json")
    force_authenticate(request, user=customer_user)
    response = RentalCreateView.as_view()(request)
    assert response.status_code == 201
    assert Rental.objects.count() == 1
    rental = Rental.objects.first()
    assert str(rental.total_cost) == "200.00"


@pytest.mark.django_db
def test_create_rental_overlap(factory, customer_user, customer, car):
    Rental.objects.create(
        customer=customer,
        car=car,
        start_date=date(2024, 3, 1),
        end_date=date(2024, 3, 5),
        total_cost=Decimal("500.00"),
        status="pending",
    )
    data = {
        "car": car.id,
        "start_date": "2024-03-04",
        "end_date": "2024-03-06",
    }
    request = factory.post("/rentals/create/", data, format="json")
    force_authenticate(request, user=customer_user)
    response = RentalCreateView.as_view()(request)
    assert response.status_code == 400
    assert Rental.objects.count() == 1


@pytest.mark.django_db
def test_get_rental_detail_success(factory, owner_user, customer, customer_user, car):
    rental = Rental.objects.create(
        customer=customer,
        car=car,
        start_date=date(2024, 4, 1),
        end_date=date(2024, 4, 2),
        total_cost=Decimal("200.00"),
        status="pending",
    )

    request = factory.get(f"/rentals/{rental.id}/")
    force_authenticate(request, user=owner_user)
    response = RentalDetailView.as_view()(request, pk=rental.id)

    assert response.status_code == 200
    assert response.data["id"] == rental.id
    assert response.data["customer"]["id"] == customer.id


@pytest.mark.django_db
def test_change_password_incorrect_old_password(factory, customer_user):
    request = factory.put(
        "/password-change/",
        {"old_password": "wrongpassord", "new_password": "newpassword123"},
        format="json",
    )
    force_authenticate(request, user=customer_user)
    response = ChangePasswordView.as_view()(request)
    assert response.status_code == 400
    assert "message" in response.data
