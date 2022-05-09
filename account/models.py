import binascii
import os

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password, **other_fields):
        other_fields.setdefault("is_active", True)
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)

        if other_fields.get("is_staff") is not True:
            raise ValueError("Superuser must be assigned to is_staff=True")

        elif other_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must be assigned to is_superuser=True")
        return self.create_user(email, password, **other_fields)

    def create_user(self, email, password, **other_fields):
        if not email:
            raise ValueError("You must provide an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="Email address",
        help_text="Required",
        max_length=128,
        unique=True,
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    requests_limit = models.IntegerField(default=-1)
    objects = CustomUserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_user_requests_limit_constraint",
                check=models.Q(requests_limit__gte=-1),
            )
        ]


class Application(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField(verbose_name="IP", null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=1024, null=True, blank=True)
    image = models.ImageField(
        upload_to="applications/%Y/%m/%d", null=True, blank=True
    )
    requests_limit = models.IntegerField(default=-1)
    token = models.CharField(max_length=255, db_index=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}, {self.created_on.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        return super().save(*args, **kwargs)

    @staticmethod
    def generate_token():
        return binascii.hexlify(os.urandom(32)).decode()

    @property
    def image_url(self):
        if self.image:
            return f"{settings.HOST}{settings.MEDIA_URL}{self.image.url}"
        return None

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_user_requests_limit_constraint",
                check=models.Q(requests_limit__gte=-1),
            )
        ]


class Category(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class EndpointChoices(models.IntegerChoices):
    get = 1, "GET"
    post = 2, "POST"
    put = 3, "PUT"
    delete = 4, "DELETE"
    patch = 5, "PATCH"


class Endpoint(models.Model):
    url = models.CharField(max_length=64)
    name = models.CharField(max_length=32)
    description = models.TextField(max_length=512)
    method = models.IntegerField(choices=EndpointChoices.choices, default=1)

    def __str__(self):
        return self.url

    class Meta:
        ordering = ("id",)


class API(models.Model):
    parent = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="apis"
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    short_description = models.CharField(max_length=128)
    long_description = models.TextField(max_length=1024, null=True, blank=True)
    image = models.ImageField(upload_to="api/%Y/%m/%d", null=True, blank=True)
    terms_of_use = models.TextField(max_length=2048, null=True, blank=True)
    base_url = models.URLField()
    endpoints = models.ManyToManyField(Endpoint, blank=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        if self.image:
            return f"{settings.HOST}{self.image.url}"
        return None

    class Meta:
        ordering = ("id",)
        verbose_name = "API"
        verbose_name_plural = "APIs"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_app(sender, instance=None, created=False, **kwargs):
    if created:
        Application.objects.create(
            owner=instance, name=f"default-application_{instance.pk}"
        )
