from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser, PermissionsMixin, AbstractBaseUser
from .managers import CustomUserManager
from django.db import models
from django.db.models.fields import CharField
from phone_field import PhoneField
from django.core.validators import MaxLengthValidator, MinLengthValidator, MinValueValidator, MaxValueValidator
import datetime
from django.db.models import Q


def current_year():
    return datetime.date.today().year


class User(AbstractBaseUser, PermissionsMixin):
    """
    Represents a user that extends the default Django AbstractUser with additional attributes.

    This class extends the `AbstractBaseUser` for custom authentication handling and
    `PermissionsMixin` for adding permissions hierarchy. It is designed to support
    both customer and administrative roles but enforces they cannot overlap. It
    includes essential attributes such as email and phone number for identification
    and contact purposes.

    :ivar first_name: The first name of the user.
    :type first_name: str
    :ivar last_name: The last name of the user.
    :type last_name: str
    :ivar email: The unique email address of the user, used as the username field.
    :type email: str
    :ivar is_owner: Indicates whether the user has administrative privileges within
        the system.
    :type is_owner: bool
    :ivar is_staff: Indicates whether the user has staff-level access permissions.
    :type is_staff: bool
    """

    first_name = CharField(max_length=50, blank=True)
    last_name = CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    is_owner = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        if self.first_name and self.last_name:
            return self.first_name + " " + self.last_name
        return self.email


class Customer(models.Model):
    """
    Represents a Candidate entity.
    Extends the base user model via a one-to-one relationship.

    :ivar user: One-to-one relationship with the User model.
    :type user: User
    :ivar date_of_birth: The date of birth of the customer.
    :type date_of_birth: DateField
    :ivar licence_expiry_date: The expiry date of the customer's driving licence.
    :type licence_expiry_date: DateField
    :ivar licence_since: The date since the customer has had a driving licence.
    :type licence_since: str
    :ivar address: The address of the customer.
    :type address: str
    :ivar city: The city of the customer.
    :type city: str
    :ivar country: The country of the customer.
    :type country: str
    :ivar citizenship: The citizenship of the customer.
    :type citizenship: str
    :ivar phone_number: The unique phone number of the user.
    :type phone_number: str
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    licence_expiry_date = models.DateField()
    licence_since = models.DateField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    citizenship = models.CharField(max_length=255)
    phone_number = PhoneField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}" if self.user else "Customer without user"


class Car(models.Model):
    """
    Represents a car available for rental.

    :ivar brand: Name of the car's brand.
    :type brand: CharField
    :ivar model: Name of the car's model.
    :type model: CharField
    :ivar description: A text description of the car.
    :type description: TextField
    :ivar production_year: The year the car was produced
    :type production_year: PositiveIntegerField
    :ivar mileage: The mileage of the car.
    :type mileage: PositiveIntegerField
    :ivar vin: The Vehicle Identification Number of the car.
    :type vin: CharField
    :ivar daily_rate: The daily rental rate for the car.
    :type daily_rate: DecimalField
    :ivar availability: A boolean flag indicating whether the car is available for
        rental.
    :type availability: BooleanField
    """
    brand = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    description = models.TextField()
    production_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1886), MaxValueValidator(current_year())])
    mileage = models.PositiveIntegerField()
    vin = models.CharField(max_length=255, unique=True,
                           validators=[MinLengthValidator(17), MaxLengthValidator(17)])
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.BooleanField(default=True)

    def __str__(self):
        return self.brand + " " + self.model


class Rental(models.Model):
    """
    Represents a rental transaction for a car rental service.

    :ivar customer: The customer related to the rental.
    :type customer: Customer
    :ivar car: The car being rented.
    :type car: Car
    :ivar start_date: The date on which the rental period begins.
    :type start_date: date
    :ivar end_date: The date on which the rental period ends.
    :type end_date: date
    :ivar return_date: The actual date the car is returned. Null if not yet returned.
    :type return_date: date or None
    :ivar total_cost: The total cost of the rental.
    :type total_cost: Decimal
    :ivar status: The current status of the rental. Choices include "pending",
        "confirmed", "completed", and "cancelled".
    :type status: str
    :ivar created_at: The timestamp when the rental record is created.
    :type created_at: datetime
    """
    status_enum = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=status_enum, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rental of {self.car} by {self.customer}"


class Payment(models.Model):
    """
    This class is used to record and manage details of payments made for rentals.

    :ivar rental: Rental instance associated with the payment.
    :type rental: Rental
    :ivar amount: Payment amount.
    :type amount: DecimalField
    :ivar payment_date: Date and time when the payment was made.
    :type payment_date: DateTimeField
    :ivar status: Status of the payment ('pending', 'completed', 'failed').
    :type status: CharField
    """
    status_enum = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=status_enum, default='pending')

    def __str__(self):
        return f"Payment of {self.amount} for {self.rental}"
