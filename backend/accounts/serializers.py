from __future__ import annotations

from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from readyby.validation import validate_phone

from .models import MAX_NAME_LENGTH, User

#: Longest password ReadyBy accepts. Bounded so a password can never be a
#: multi-megabyte hashing cost, which is a denial-of-service vector rather than
#: a helpful limit.
MAX_PASSWORD_LENGTH = 128


def field_error(field: str, message: str) -> serializers.ValidationError:
    return serializers.ValidationError({field: [message]})


class UserSerializer(serializers.ModelSerializer):
    """What a signed-in user may see about themselves.

    Exposes the account fields a person owns (name, phone) plus the two facts
    they need to know about the account itself: its status and when it was
    created. Deliberately excludes ``is_staff``, ``is_superuser`` and the
    password hash.
    """

    display_name = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    cafe = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "display_name",
            "initials",
            "role",
            "phone",
            "status",
            "is_active",
            "created_at",
            "cafe",
        )
        read_only_fields = (
            "id",
            "email",
            "role",
            "status",
            "is_active",
            "created_at",
            "cafe",
        )

    def get_cafe(self, user: User) -> dict | None:
        cafe = getattr(user, "cafe", None)
        if cafe is None:
            return None
        return {"slug": cafe.slug, "name": cafe.name, "is_active": cafe.is_active}


class PublicUserSerializer(serializers.ModelSerializer):
    """The safe subset shown to the café on its own order ticket.

    A café needs to greet the customer and reach them if the order is wrong, and
    nothing more: no account status, no role, no internal ids.
    """

    display_name = serializers.CharField(source="full_name", read_only=True)

    class Meta:
        model = User
        fields = ("display_name", "phone")
        read_only_fields = fields


def _clean_phone(value: str) -> str:
    """Normalise and validate a phone number, as a field error."""
    phone = (value or "").strip()
    try:
        validate_phone(phone)
    except DjangoValidationError as exc:
        raise field_error("phone", exc.messages[0]) from exc
    return phone


def _split_confirmed_password(attrs: dict) -> dict:
    """Require ``confirm_password`` to match ``password``.

    The check lives on the server as well as in the browser: a form-only check
    is trivially bypassed, and a mismatched confirmation is a typo that would
    otherwise lock the customer out of their own new account.
    """
    password = attrs.get("password")
    confirm = attrs.pop("confirm_password", None)

    if confirm is None:
        raise field_error(
            "confirm_password", "Please confirm your password so we know it is right."
        )
    if password is not None and confirm != password:
        raise field_error("confirm_password", "The two passwords do not match.")
    return attrs


class RegisterSerializer(serializers.Serializer):
    """Customer self-registration.

    ``role`` is intentionally not accepted: a customer must never be able to
    create a merchant or admin account. Merchant accounts are created by a
    ReadyBy admin through Django admin.
    """

    first_name = serializers.CharField(max_length=MAX_NAME_LENGTH)
    last_name = serializers.CharField(
        max_length=MAX_NAME_LENGTH,
        required=False,
        allow_blank=True,
        default="",
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH
    )
    confirm_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH
    )
    phone = serializers.CharField(
        max_length=32, required=False, allow_blank=True, default=""
    )

    def validate_email(self, value: str) -> str:
        email = User.objects.normalize_email(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "An account with this email already exists. Try signing in instead."
            )
        return email

    def validate_first_name(self, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise serializers.ValidationError("Please enter your first name.")
        return name

    def validate_last_name(self, value: str) -> str:
        name = value.strip()
        # A surname is optional; only a too-short one is a mistake.
        if name and len(name) < 2:
            raise serializers.ValidationError(
                "That last name looks too short. Check it for a typo."
            )
        return name

    def validate_phone(self, value: str) -> str:
        return _clean_phone(value)

    def validate_password(self, value: str) -> str:
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs: dict) -> dict:
        return _split_confirmed_password(attrs)

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        return User.objects.create_user(
            role=User.Role.CUSTOMER,
            status=User.Status.ACTIVE,
            password=password,
            **validated_data,
        )


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """What a signed-in person may change about their own account.

    Only the fields the account owner owns are writable. ``role``, ``cafe``,
    ``status`` and the email address are deliberately absent from
    ``Meta.fields``: a payload naming them is ignored rather than applied, so a
    crafted request cannot promote a customer to merchant or un-suspend a
    suspended account.
    """

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        required=False,
        max_length=MAX_PASSWORD_LENGTH,
        help_text="Leave blank to keep your current password.",
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        required=False,
        max_length=MAX_PASSWORD_LENGTH,
    )
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        required=False,
        max_length=MAX_PASSWORD_LENGTH,
        help_text="Required when changing your password.",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "password",
            "confirm_password",
            "current_password",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": False, "allow_blank": True},
            "phone": {"required": False, "allow_blank": True},
        }

    def validate_first_name(self, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise serializers.ValidationError("Please enter your first name.")
        return name

    def validate_last_name(self, value: str) -> str:
        name = value.strip()
        if name and len(name) < 2:
            raise serializers.ValidationError(
                "That last name looks too short. Check it for a typo."
            )
        return name

    def validate_phone(self, value: str) -> str:
        return _clean_phone(value)

    def validate_password(self, value: str) -> str:
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs: dict) -> dict:
        password = attrs.get("password")
        confirm = attrs.pop("confirm_password", None)
        current = attrs.get("current_password")

        if password:
            # Changing a password is the one dangerous thing a stolen session can
            # do, so it needs the current one. Compared with the existing hash,
            # so the real password never has to be stored or sent again.
            if not current or not self.instance.check_password(current):
                raise field_error(
                    "current_password", "Your current password is not correct."
                )
            if not confirm:
                raise field_error(
                    "confirm_password", "Please confirm your new password."
                )
            if confirm != password:
                raise field_error("confirm_password", "The two passwords do not match.")
        else:
            # A confirmation without a new password is a half-finished form.
            if confirm or current:
                raise field_error(
                    "password", "Enter a new password to change it."
                )

        attrs.pop("current_password", None)
        return attrs

    def update(self, instance: User, validated_data: dict) -> User:
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=MAX_PASSWORD_LENGTH
    )

    def validate(self, attrs: dict) -> dict:
        email = User.objects.normalize_email(attrs["email"])
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            # One message for both cases: never reveal whether an account exists.
            raise serializers.ValidationError(
                {"non_field_errors": ["Incorrect email or password."]}
            )
        attrs["user"] = user
        return attrs


def ensure_token(user: User):
    """Return the user's API token, creating one on first login."""
    from rest_framework.authtoken.models import Token

    token, _ = Token.objects.get_or_create(user=user)
    return token