from django.contrib import admin
from .models import *

admin.site.register([
    User,
    Customer,
    Car,
    Accessory,
    Rental,
    Payment
])
