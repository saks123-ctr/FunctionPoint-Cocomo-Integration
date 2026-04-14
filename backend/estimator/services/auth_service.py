"""User registration and related auth helpers (no HTTP concerns)."""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

User = get_user_model()


@dataclass(frozen=True)
class RegisteredUser:
    """Result of a successful registration."""

    user: User


class RegistrationError(Exception):
    """Raised when registration cannot complete (duplicate identity, etc.)."""


def register_user(*, username: str, password: str, email: str = "") -> RegisteredUser:
    """
    Create a new user account. Username must be unique; email is optional but must be unique if set.

    Raises RegistrationError for business-rule violations, ValidationError for invalid model data.
    """
    username_clean = (username or "").strip()
    if not username_clean:
        raise RegistrationError("Username is required.")

    email_clean = (email or "").strip()
    if User.objects.filter(username__iexact=username_clean).exists():
        raise RegistrationError("That username is already taken.")
    if email_clean and User.objects.filter(email__iexact=email_clean).exists():
        raise RegistrationError("That email is already registered.")

    try:
        user = User.objects.create_user(
            username=username_clean,
            email=email_clean,
            password=password,
        )
    except (IntegrityError, DjangoValidationError) as exc:
        raise RegistrationError("Could not create account.") from exc

    return RegisteredUser(user=user)
