from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Manager class for a custom user model.
    This class provides methods to create regular users and superusers. It overrides
    the base manager functionalities to include custom user creation logic.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and returns a user with the specified email, password, and any additional
        fields.

        :param email: The email address for the user.
        :type email: str
        :param password: The password for the user, could be None.
        :type password: str
        :param extra_fields: Additional optional fields to be associated with the user.
        :type extra_fields: dict | None | Boolean
        :return: The created user object.
        :rtype: self.model
        :raises ValueError: If the email is not provided.
        """
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and returns a superuser with the given email, password, and additional
        fields.

        :param email: The email address of the superuser.
        :type email: str
        :param password: The password for the superuser.
        :type password: str
        :param extra_fields: Additional attributes to be assigned to the superuser.
        :type extra_fields: dict | None | Boolean
        :return: The created superuser instance.
        :rtype: self.model
        :raises ValueError: If the email is not provided.
        :raises ValueError: If 'is_staff' is not set to True in extra_fields.
        :raises ValueError: If 'is_superuser' is not set to True in extra_fields.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
