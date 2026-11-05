"""User model for the ReadyBy pilot.

Three roles only: CUSTOMER (the person ordering), MERCHANT (the person running a
café) and ADMIN (ReadyBy staff who onboard cafés through Django admin).
"""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinLengthValidator
from django.db import models

from readyby.validation import validate_phone

from .managers import UserManager

#: A first or last name shorter than this is not a name. Two characters covers
#: "Bo", "Ng" and "Ali" without accepting a stray keystroke as a whole name.
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 80

name_validators = [MinLengthValidator(MIN_NAME_LENGTH)]


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        MERCHANT = "MERCHANT", "Merchant"
        ADMIN = "ADMIN", "Admin"

    class Status(models.TextChoices):
        """The customer-facing account status.

        ``ACTIVE`` is the only state an account can sign in from, so the two are
        deliberately separate: suspending an account must never leave a stale
        ``ACTIVE`` behind, and the status a customer sees ("suspended") is more
        useful to them than the boolean.
        """

        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    email = models.EmailField(unique=True)
    first_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        validators=name_validators,
    )
    last_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        blank=True,
        validators=name_validators,
    )
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )
    phone = models.CharField(max_length=32, blank=True, validators=[validate_phone])
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    class Meta:
        ordering = ["email"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["CUSTOMER", "MERCHANT", "ADMIN"]),
                name="user_role_is_known",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["ACTIVE", "SUSPENDED"]),
                name="user_status_is_known",
            ),
            # Sign-in requires both flags, so they can never disagree.
            models.CheckConstraint(
                condition=models.Q(is_active=True, status="ACTIVE")
                | models.Q(is_active=False, status="SUSPENDED"),
                name="user_status_matches_is_active",
            ),
        ]

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        self.email = UserManager.normalize_email(self.email)
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        self.phone = (self.phone or "").strip()
        self.sync_active_status()

    def save(self, *args, **kwargs) -> None:
        # Keep the two account-state columns in step no matter which one a caller
        # set, so a suspended account can never still be flagged active.
        self.sync_active_status()
        super().save(*args, **kwargs)

    def sync_active_status(self) -> None:
        """Derive ``status`` from ``is_active`` (or the other way round).

        Django's admin, a management command and a test may all set either
        field. Rather than making every caller remember the other one, this
        resolves the pair here and the database constraint enforces the result.
        """
        if self.is_active and self.status != self.Status.ACTIVE:
            self.status = self.Status.ACTIVE
        elif not self.is_active and self.status != self.Status.SUSPENDED:
            self.status = self.Status.SUSPENDED

    def set_suspended(self, suspended: bool = True) -> None:
        """Suspend or restore the account, keeping both columns consistent."""
        self.is_active = not suspended
        self.status = self.Status.SUSPENDED if suspended else self.Status.ACTIVE
        self.save(update_fields=["is_active", "status", "updated_at"])

    @property
    def full_name(self) -> str:
        """The person's name as one string.

        Derived, never stored: keeping a second copy of the name would let the
        two disagree.
        """
        return " ".join(part for part in (self.first_name, self.last_name) if part)

    @property
    def display_name(self) -> str:
        if self.full_name:
            return self.full_name
        return self.email.split("@", 1)[0]

    @property
    def initials(self) -> str:
        """Up to two letters, for the places the UI shows a person by name."""
        letters = [
            part[0] for part in (self.first_name, self.last_name) if part
        ]
        return "".join(letters).upper()

    @property
    def is_customer(self) -> bool:
        return self.role == self.Role.CUSTOMER

    @property
    def is_merchant(self) -> bool:
        return self.role == self.Role.MERCHANT

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser