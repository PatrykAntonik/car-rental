import datetime

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

     :ivar first_name: The first name of the user.
     :type first_name: str
     :ivar last_name: The last name of the user.
     :type last_name: str
     :ivar email: The email address of the user.
     :type email: str
     :ivar password: The hashed password of the user.
     :type password: str
     :ivar phone_number: The phone number of the user. Must be unique.
     :type phone_number: PhoneField
     :ivar is_customer: Flag to indicate if the user is a customer. Defaults to False.
     :type is_customer: bool
     :ivar is_admin: Flag to indicate if the user is an admin/owner. Defaults to False.
     :type is_admin: bool
     """

    first_name = CharField(max_length=50, blank=True)
    last_name = CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = PhoneField(max_length=255, unique=True)
    is_customer = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~(Q(is_customer=True) & Q(is_admin=True)),
                name='chk_user_not_both_roles'
            )
        ]

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
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    licence_expiry_date = models.DateField()
    licence_since = models.DateField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    citizenship = models.CharField(max_length=255)


class Car(models.Model):
    """
    Represents a Car entity.
    :ivar brand: The brand of the car.
    :type brand: str
    :ivar model: The model of the car.
    :type model: str
    :ivar production_year: The year the car was produced.
    :type production_year: int
    :ivar mileage: The mileage of the car.
    :type mileage: int
    :ivar vin: The Vehicle Identification Number (VIN) of the car.
    :type vin: str
    :ivar daily_rate: The daily rental rate of the car.
    :type daily_rate: int
    :ivar availability: Flag to indicate if the car is available for rent. Defaults to True.
    :type availability: bool
    :ivar description: A description of the car.
    :type description: str
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


class Accessory(models.Model):
    """
    Represents an Accessory entity.
    :ivar name: The name of the accessory.
    :type name: str
    :ivar description: A description of the accessory.
    :type description: str
    :ivar daily_rate: The daily rental rate of the accessory.
    :type daily_rate: int
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    daily_rate = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Rental(models.Model):
    """
    Represents a Rental entity.
    :ivar customer: The customer who rented the car.
    :type customer: Customer
    :ivar car: The car that was rented.
    :type car: Car
    :ivar start_date: The start date of the rental.
    :type start_date: DateField
    :ivar end_date: The end date of the rental.
    :type end_date: DateField
    :ivar total_cost: The total cost of the rental.
    :type total_cost: int
    :ivar accessories: The accessories rented with the car.
    :type accessories: ManyToManyField
    :ivar status: The status of the rental (e.g., pending, confirmed, completed, cancelled).
    :type status: str
    :ivar created_at: Date when Rental was created
    :type: DateField
    """
    status_enum = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    accessories = models.ManyToManyField(Accessory, blank=True)
    status = models.CharField(max_length=50, choices=status_enum, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rental of {self.car} by {self.customer}"


class Payment(models.Model):
    """
    Represents a Payment entity.
    :ivar rental: The rental associated with the payment.
    :type rental: Rental
    :ivar amount: The amount paid.
    :type amount: DecimalField
    :ivar payment_date: The date of the payment.
    :type payment_date: DateTimeField
    :ivar payment_method: The method of payment (e.g., credit card, cash).
    :type payment_method: str
    """
    status_enum = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=status_enum, default='pending')

    def __str__(self):
        return f"Payment of {self.amount} for {self.rental}"
