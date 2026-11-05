"""Split the stored ``full_name`` into the new first/last name pair.

Every existing account keeps the name it already had: the old single column is
read, split on the first space and written to the two new columns before the
old column is dropped. A one-word name becomes a first name with no surname,
which is how the form treats it too.

The status backfill runs here as well so a pre-existing ``is_active=False``
account is labelled SUSPENDED rather than being left contradicting the new
database constraint.
"""

from __future__ import annotations

import django.core.validators
import django.utils.timezone
import readyby.validation
from django.db import migrations, models


def split_names(apps, schema_editor):
    """Copy each account's full name into first_name / last_name."""
    User = apps.get_model("accounts", "User")

    pending = User.objects.exclude(full_name="").only("id", "full_name")
    rows = []
    for user in pending.iterator():
        parts = [part for part in (user.full_name or "").strip().split() if part]
        if len(parts) == 1:
            first, last = parts[0], ""
        else:
            first, last = parts[0], " ".join(parts[1:])
        rows.append(User(id=user.id, first_name=first[:80], last_name=last[:80]))

    if rows:
        User.objects.bulk_update(rows, ["first_name", "last_name"])


def sync_status(apps, schema_editor):
    """Make the new status column agree with the existing is_active flag."""
    User = apps.get_model("accounts", "User")
    User.objects.filter(is_active=True, status="SUSPENDED").update(status="ACTIVE")
    User.objects.filter(is_active=False, status="ACTIVE").update(status="SUSPENDED")


def noop(apps, schema_editor):
    """Nothing to undo: the reverse step restores the old column, empty."""


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        # The old column is read before it goes, so the order here matters.
        migrations.AddField(
            model_name="user",
            name="first_name",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="user",
            name="last_name",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="user",
            name="status",
            field=models.CharField(
                choices=[("ACTIVE", "Active"), ("SUSPENDED", "Suspended")],
                db_index=True,
                default="ACTIVE",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="updated_at",
            # ``updated_at`` is NOT NULL, and SQLite cannot add a NOT NULL column
            # to a table that already has rows: it has to rebuild the table and
            # copy every old row across. With ``default=None`` the copy writes
            # NULL into the new column and the whole migration dies with
            # "NOT NULL constraint failed", leaving the accounts table on the
            # old schema - which breaks sign in and sign up with a 500.
            # A real value is needed for the copy to succeed, and "when this row
            # was last written, as far as we knew" is as honest a backfill as
            # exists: the previous column set cannot be recovered.
            field=models.DateTimeField(
                auto_now=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.RunPython(split_names, noop),
        migrations.RunPython(sync_status, noop),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(
                blank=True,
                max_length=80,
                validators=[django.core.validators.MinLengthValidator(2)],
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(
                blank=True,
                max_length=80,
                validators=[django.core.validators.MinLengthValidator(2)],
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=models.CharField(blank=True, max_length=32, validators=[readyby.validation.validate_phone]),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(("status__in", ["ACTIVE", "SUSPENDED"])),
                name="user_status_is_known",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("is_active", True), ("status", "ACTIVE")),
                    models.Q(("is_active", False), ("status", "SUSPENDED")),
                    _connector="OR",
                ),
                name="user_status_matches_is_active",
            ),
        ),
        # Last, once every row has been copied across.
        migrations.RemoveField(
            model_name="user",
            name="full_name",
        ),
    ]