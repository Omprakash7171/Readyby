"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import {
  BadgeCheck,
  CalendarDays,
  KeyRound,
  Mail,
  Store,
  UserRound,
} from "lucide-react";
import { ApiError, updateMe } from "@/lib/api";
import type { ApiUser } from "@/lib/apiTypes";
import { useRequireSession } from "@/context/SessionProvider";
import { Badge } from "@/components/ui/Badge";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";

const ROLE_LABEL = {
  CUSTOMER: "Customer",
  MERCHANT: "Café owner",
  ADMIN: "ReadyBy admin",
} as const;

function fieldErrorsFrom(err: unknown): Record<string, string[]> {
  return err instanceof ApiError ? err.fieldErrors : {};
}

function messageFrom(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

function FormNotice({
  error,
  saved,
  savedMessage,
}: {
  error: string | null;
  saved: boolean;
  savedMessage: string;
}) {
  if (error) {
    return (
      <p
        role="alert"
        className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        {error}
      </p>
    );
  }
  if (saved) {
    return (
      <p
        role="status"
        className="rounded-2xl border border-ready-200 bg-ready-50 px-4 py-3 text-sm text-ready-700"
      >
        {savedMessage}
      </p>
    );
  }
  return null;
}

export default function AccountPage() {
  const session = useRequireSession();

  if (session.pending || !session.user) return null;

  return <AccountView user={session.user} onUpdated={session.updateUser} />;
}

function AccountView({
  user,
  onUpdated,
}: {
  user: ApiUser;
  onUpdated: (user: ApiUser) => void;
}) {
  const memberSince = new Date(user.created_at).toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });

  return (
    <div className="mx-auto w-full max-w-5xl px-5 py-10 sm:py-14">
      <header>
        <p className="text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
          Your account
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-5xl">
          Account settings
        </h1>
        <p className="mt-3 text-pretty text-base text-ink-500">
          Keep your name and phone number up to date so the café can reach you.
        </p>
      </header>

      <div className="mt-9 grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-6">
          <ProfileCard user={user} onUpdated={onUpdated} />
          <PasswordCard onUpdated={onUpdated} />
        </div>

        <aside className="space-y-4">
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <span
                aria-hidden
                className="inline-flex size-12 items-center justify-center rounded-full bg-ink-900 text-base font-semibold text-white"
              >
                {user.initials || user.display_name.slice(0, 2).toUpperCase()}
              </span>
              <div className="min-w-0">
                <p className="truncate font-semibold text-ink-900">{user.display_name}</p>
                <p className="truncate text-sm text-ink-500">{user.email}</p>
              </div>
            </div>

            <dl className="mt-6 space-y-4 text-sm">
              <div className="flex items-center gap-2.5">
                <BadgeCheck className="size-4 text-ink-400" aria-hidden />
                <dt className="sr-only">Role</dt>
                <dd>
                  <Badge tone={user.role === "MERCHANT" ? "brand" : "neutral"}>
                    {ROLE_LABEL[user.role]}
                  </Badge>
                </dd>
              </div>
              <div className="flex items-center gap-2.5 text-ink-600">
                <CalendarDays className="size-4 text-ink-400" aria-hidden />
                <dt className="sr-only">Member since</dt>
                <dd>Member since {memberSince}</dd>
              </div>
              <div className="flex items-center gap-2.5 text-ink-600">
                <Mail className="size-4 text-ink-400" aria-hidden />
                <dt className="sr-only">Email</dt>
                <dd className="truncate">{user.email}</dd>
              </div>
              {user.role === "MERCHANT" && user.cafe ? (
                <div className="flex items-center gap-2.5 text-ink-600">
                  <Store className="size-4 text-ink-400" aria-hidden />
                  <dt className="sr-only">Your café</dt>
                  <dd className="truncate">{user.cafe.name}</dd>
                </div>
              ) : null}
            </dl>

            <p className="mt-6 rounded-2xl bg-ink-50 px-4 py-3 text-xs leading-relaxed text-ink-500">
              Your email address is how you sign in, so it can&rsquo;t be changed here.
            </p>
          </Card>

          <div className="flex flex-col gap-2.5">
            <ButtonLink href="/orders" variant="secondary" fullWidth>
              View my orders
            </ButtonLink>
            {user.role === "MERCHANT" ? (
              <ButtonLink href="/merchant" variant="secondary" fullWidth>
                Go to my café board
              </ButtonLink>
            ) : (
              <ButtonLink href="/explore" variant="secondary" fullWidth>
                Find nearby cafés
              </ButtonLink>
            )}
          </div>

          <p className="px-1 text-xs text-ink-400">
            Need something else?{" "}
            <Link href="/" className="font-medium text-brand-600 underline underline-offset-4">
              Back to ReadyBy
            </Link>
          </p>
        </aside>
      </div>
    </div>
  );
}

function ProfileCard({
  user,
  onUpdated,
}: {
  user: ApiUser;
  onUpdated: (user: ApiUser) => void;
}) {
  const [firstName, setFirstName] = useState(user.first_name);
  const [lastName, setLastName] = useState(user.last_name);
  const [phone, setPhone] = useState(user.phone);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setFieldErrors({});
    setSaved(false);
    try {
      const updated = await updateMe({
        first_name: firstName,
        last_name: lastName,
        phone,
      });
      onUpdated(updated);
      setSaved(true);
    } catch (err) {
      setError(messageFrom(err, "We couldn't save your details. Please try again."));
      setFieldErrors(fieldErrorsFrom(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="p-6 sm:p-8">
      <div className="flex items-center gap-3">
        <span className="inline-flex size-10 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <UserRound className="size-5" aria-hidden />
        </span>
        <div>
          <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
            Your details
          </h2>
          <p className="text-sm text-ink-500">
            The name and number the café sees on your ticket.
          </p>
        </div>
      </div>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-5" noValidate>
        <FormNotice error={error} saved={saved} savedMessage="Your details are saved." />

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="First name" htmlFor="first_name">
            <Input
              id="first_name"
              name="first_name"
              autoComplete="given-name"
              required
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              aria-invalid={Boolean(fieldErrors.first_name)}
            />
            {fieldErrors.first_name?.map((message) => (
              <p key={message} className="text-xs text-red-600">
                {message}
              </p>
            ))}
          </Field>

          <Field label="Last name" htmlFor="last_name" hint="Optional.">
            <Input
              id="last_name"
              name="last_name"
              autoComplete="family-name"
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
              aria-invalid={Boolean(fieldErrors.last_name)}
            />
            {fieldErrors.last_name?.map((message) => (
              <p key={message} className="text-xs text-red-600">
                {message}
              </p>
            ))}
          </Field>
        </div>

        <Field
          label="Phone"
          htmlFor="phone"
          hint="Used only if the café needs to reach you about an order."
        >
          <Input
            id="phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
            aria-invalid={Boolean(fieldErrors.phone)}
          />
          {fieldErrors.phone?.map((message) => (
            <p key={message} className="text-xs text-red-600">
              {message}
            </p>
          ))}
        </Field>

        <div className="flex justify-end">
          <Button type="submit" variant="dark" disabled={saving}>
            {saving ? "Saving…" : "Save details"}
          </Button>
        </div>
      </form>
    </Card>
  );
}

function PasswordCard({ onUpdated }: { onUpdated: (user: ApiUser) => void }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setFieldErrors({});
    setSaved(false);
    try {
      const updated = await updateMe({
        current_password: currentPassword,
        password: newPassword,
        confirm_password: confirmPassword,
      });
      onUpdated(updated);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setSaved(true);
    } catch (err) {
      setError(messageFrom(err, "We couldn't change your password. Please try again."));
      setFieldErrors(fieldErrorsFrom(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="p-6 sm:p-8">
      <div className="flex items-center gap-3">
        <span className="inline-flex size-10 items-center justify-center rounded-full bg-ink-100 text-ink-700">
          <KeyRound className="size-5" aria-hidden />
        </span>
        <div>
          <h2 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
            Password
          </h2>
          <p className="text-sm text-ink-500">
            Choose something you don&rsquo;t use anywhere else.
          </p>
        </div>
      </div>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-5" noValidate>
        <FormNotice
          error={error}
          saved={saved}
          savedMessage="Your password has been changed."
        />

        <Field label="Current password" htmlFor="current_password">
          <Input
            id="current_password"
            name="current_password"
            type="password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            aria-invalid={Boolean(fieldErrors.current_password)}
          />
          {fieldErrors.current_password?.map((message) => (
            <p key={message} className="text-xs text-red-600">
              {message}
            </p>
          ))}
        </Field>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="New password" htmlFor="password">
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              aria-invalid={Boolean(fieldErrors.password)}
            />
            {fieldErrors.password?.map((message) => (
              <p key={message} className="text-xs text-red-600">
                {message}
              </p>
            ))}
          </Field>

          <Field label="Confirm new password" htmlFor="confirm_password">
            <Input
              id="confirm_password"
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              aria-invalid={Boolean(fieldErrors.confirm_password)}
            />
            {fieldErrors.confirm_password?.map((message) => (
              <p key={message} className="text-xs text-red-600">
                {message}
              </p>
            ))}
          </Field>
        </div>

        <div className="flex justify-end">
          <Button type="submit" variant="outline" disabled={saving}>
            {saving ? "Updating…" : "Change password"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
