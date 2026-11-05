from __future__ import annotations

from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User
from django.db import models


def normalise_email(raw: str) -> str:
    return (raw or "").strip().lower()


def split_name(full_name: str) -> dict[str, str]:
    """Split a single name string into first and last.

    "Casey Customer" -> first "Casey", last "Customer". A single word is treated
    as a first name, which is how people fill in a form when they have no
    surname to give. Exists so callers that already hold one name string (the
    demo seeder, tests) keep working now that the two names are stored apart.
    """
    parts = [part for part in (full_name or "").strip().split() if part]
    if not parts:
        return {"first_name": "", "last_name": ""}
    if len(parts) == 1:
        return {"first_name": parts[0], "last_name": ""}
    return {"first_name": parts[0], "last_name": " ".join(parts[1:])}


class UserManager(BaseUserManager):
    """Creates users keyed on a lower-cased email address."""

    use_in_migrations = True

    normalize_email = staticmethod(normalise_email)

    def _create_user(self, email: str, password: str, **extra: Any) -> User:
        if not email:
            raise ValueError("An email address is required.")

        # ``full_name`` is accepted for backwards compatibility with callers
        # written before the name was split in two. It is unpacked here rather
        # than stored, so there is still only one source of truth.
        full_name = extra.pop("full_name", None)
        if full_name is not None and "first_name" not in extra:
            extra.update(split_name(full_name))

        user = self.model(email=normalise_email(email), **extra)
        user.set_password(password)
        user.full_clean(exclude=["password", "last_login"])
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra: Any) -> User:
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(
        self, email: str, password: str | None = None, **extra: Any
    ) -> User:
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", User.Role.ADMIN)
        extra.setdefault("first_name", "ReadyBy")
        extra.setdefault("last_name", "Admin")
        if extra.get("is_staff") is not True or extra.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_staff and is_superuser set.")
        return self._create_user(email, password, **extra)