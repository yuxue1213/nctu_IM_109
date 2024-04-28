from django.db import models
from django.db.models import JSONField

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class AccountManager(BaseUserManager):
    def create_user(self, account, password=None, **extra_fields):
        if not account:
            raise ValueError('The Account must be set')
        user = self.model(account=account, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, account, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(account, password, **extra_fields)

class Account(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    account = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20)
    orders = JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AccountManager()

    USERNAME_FIELD = 'account'
    REQUIRED_FIELDS = ['name', 'phone_number']

    def __str__(self):
        return self.account


class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    space_id = models.IntegerField()
    phone_number = models.CharField(max_length=20)
    line_id = models.CharField(max_length=255)
    menu_list = JSONField()
    orders = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class Company(models.Model):
    name = models.CharField(max_length=255)
    members = JSONField(default=list)
    orders = JSONField(default=list)

class Member(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    orders = JSONField()

class Order(models.Model):
    items = JSONField()
    order_value = models.IntegerField()
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    member = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    last_update_time = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
