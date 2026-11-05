"use client";

import { Suspense, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useSession } from "@/context/SessionProvider";
import { customerDestination, safeNext } from "@/lib/redirects";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";

/**
 * `useSearchParams` needs a boundary above it so this route can still be
 * prerendered rather than opting the whole page out of static rendering.
 */
export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { signIn, signingIn, error, fieldErrors } = useSession();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Only follow a same-site path, so `next` can't become an open redirect.
  const next = safeNext(params.get("next"));

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const user = await signIn(email, password);
      // Café owners live in the café workspace; never drop them on the
      // customer homepage or a customer-only page.
      if (user.role === "MERCHANT") {
        const staysInWorkspace =
          next !== null &&
          (next === "/account" || next === "/merchant" || next.startsWith("/merchant/"));
        router.replace(staysInWorkspace ? next : "/merchant");
        return;
      }
      router.replace(customerDestination(next));
    } catch {
      // The session context already holds a message worth showing.
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-col px-5 py-16 sm:py-24">
      <h1 className="text-3xl font-semibold tracking-[-0.03em] text-ink-900">Sign in</h1>
      <p className="mt-3 text-ink-500">
        Sign in to place an order and follow it to the counter.
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

        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-invalid={Boolean(fieldErrors.email)}
          />
          {fieldErrors.email?.map((message) => (
            <p key={message} className="text-xs text-red-600">
              {message}
            </p>
          ))}
        </Field>

        <Field label="Password" htmlFor="password">
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>

        <Button type="submit" variant="dark" size="lg" fullWidth disabled={signingIn}>
          {signingIn ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-ink-500">
        New to ReadyBy?{" "}
        <Link
          href={next ? `/register?next=${encodeURIComponent(next)}` : "/register"}
          className="font-medium text-brand-600 underline underline-offset-4"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}