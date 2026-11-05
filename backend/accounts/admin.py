from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "phone",
        "role",
        "status",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "status", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "phone")
    readonly_fields = ("created_at", "updated_at", "last_login")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {
                "fields": ("first_name", "last_name", "phone", "role"),
                "description": "First and last name are stored separately.",
            },
        ),
        (
            "Account status",
            {
                "fields": ("status", "is_active"),
                "description": (
                    "Suspending an account signs it out everywhere and blocks "
                    "sign-in. ReadyBy keeps `status` and `is_active` in step."
                ),
            },
        ),
        (
            "Permissions",
            {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )