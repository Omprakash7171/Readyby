"use client";

import { Suspense, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useSession } from "@/context/SessionProvider";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";

/**
 * `useSearchParams` needs a boundary above it so this route can still be
 * prerendered rather than opting the whole page out of static rendering.
 */
export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <RegisterForm />
    </Suspense>
  );
}

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { signUp, signingIn, error, fieldErrors } = useSession();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});
  const next = params.get("next") ?? "/explore";

  /** The cheap checks, so a typo is caught before a round trip. */
  function validate() {
    const problems: Record<string, string> = {};
    if (firstName.trim().length < 2) problems.first_name = "Please enter your first name.";
    if (lastName.trim() && lastName.trim().length < 2) {
      problems.last_name = "That last name looks too short. Check it for a typo.";
    }
    if (password.length < 8) problems.password = "Use at least 8 characters.";
    if (confirmPassword !== password) {
      problems.confirm_password = "The two passwords do not match.";
    }
    return problems;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problems = validate();
    setLocalErrors(problems);
    if (Object.keys(problems).length > 0) return;

    try {
      await signUp({
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        password,
        confirm_password: confirmPassword,
        phone: phone.trim(),
      });
      router.replace(next.startsWith("/") && !next.startsWith("//") ? next : "/explore");
    } catch {
      // The session context already holds a message worth showing.
    }
  }

  /** Server errors win; the local message covers what the API cannot reach. */
  function message(field: string): string[] | undefined {
    return fieldErrors[field] ?? (localErrors[field] ? [localErrors[field]] : undefined);
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-col px-5 py-16 sm:py-24">
      <h1 className="text-3xl font-semibold tracking-[-0.03em] text-ink-900">
        Create your account
      </h1>
      <p className="mt-3 text-ink-500">
        Cafés use a separate sign-in. This form is for customers.
      </p>

      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-5" noValidate>
        {error ? (
          <p
            role="alert"
            className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {error}
          </p>
        ) : null}

        <div className="flex gap-3">
          <Field label="First name" htmlFor="first_name" className="flex-1">
            <Input
              id="first_name"
              name="first_name"
              autoComplete="given-name"
              required
              minLength={2}
              maxLength={60}
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
            />
            {message("first_name")?.map((text) => (
              <p key={text} className="text-xs text-red-600">
                {text}
              </p>
            ))}
          </Field>

          <Field
            label="Last name"
            htmlFor="last_name"
            hint="Optional"
            className="flex-1"
          >
            <Input
              id="last_name"
              name="last_name"
              autoComplete="family-name"
              maxLength={60}
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
            />
            {message("last_name")?.map((text) => (
              <p key={text} className="text-xs text-red-600">
                {text}
              </p>
            ))}
          </Field>
        </div>

        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          {fieldErrors.email?.map((text) => (
            <p key={text} className="text-xs text-red-600">
              {text}
            </p>
          ))}
        </Field>

        <Field label="Password" htmlFor="password" hint="At least 8 characters.">
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {message("password")?.map((text) => (
            <p key={text} className="text-xs text-red-600">
              {text}
            </p>
          ))}
        </Field>

        <Field label="Confirm password" htmlFor="confirm_password">
          <Input
            id="confirm_password"
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            required
            maxLength={128}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
          />
          {message("confirm_password")?.map((text) => (
            <p key={text} className="text-xs text-red-600">
              {text}
            </p>
          ))}
        </Field>

        <Field label="Phone" htmlFor="phone" hint="Optional — helps the café hand over quickly.">
          <Input
            id="phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            maxLength={32}
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
          {fieldErrors.phone?.map((text) => (
            <p key={text} className="text-xs text-red-600">
              {text}
            </p>
          ))}
        </Field>

        <Button type="submit" variant="dark" size="lg" fullWidth disabled={signingIn}>
          {signingIn ? "Creating your account…" : "Create account"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-ink-500">
        Already have an account?{" "}
        <Link
          href={next !== "/explore" ? `/login?next=${encodeURIComponent(next)}` : "/login"}
          className="font-medium text-brand-600 underline underline-offset-4"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}