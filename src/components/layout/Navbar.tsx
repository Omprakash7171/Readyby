"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Menu, ShoppingBag, Store, User as UserIcon } from "lucide-react";
import { cn } from "@/lib/format";
import { useBooking } from "@/context/BookingProvider";
import { useSession } from "@/context/SessionProvider";
import { Logo } from "@/components/ui/Logo";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";

const LINKS = [
  { href: "/", label: "Explore" },
  { href: "/explore", label: "Nearby" },
  { href: "/orders", label: "My Orders" },
  { href: "/login?next=%2Fmerchant", label: "For cafés" },
];

function isActive(pathname: string, href: string) {
  // Compare on the path alone: "For cafés" carries a ?next= so it can land the
  // merchant on their board, and that query must not stop it matching the page
  // it actually leads to.
  const path = href.split("?")[0];
  if (path === "/") return pathname === "/";
  return pathname.startsWith(path);
}

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { cartCount, hydrated } = useBooking();
  const { user, hydrated: sessionHydrated, signOut } = useSession();
  const [menuOpen, setMenuOpen] = useState(false);
  const onMerchant = pathname.startsWith("/merchant");
  // "For cafés" is a sign-in prompt; someone already signed in doesn't need it.
  const links = user ? LINKS.filter((link) => !link.href.startsWith("/login")) : LINKS;

  async function handleSignOut() {
    await signOut();
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-ink-100/80 bg-crema-50/85 backdrop-blur-lg">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-3 px-5">
        <Link
          href="/"
          className="shrink-0 rounded-xl transition-opacity hover:opacity-80"
          aria-label="ReadyBy home"
        >
          <Logo />
        </Link>

        <nav aria-label="Primary" className="hidden md:block">
          <ul className="flex items-center gap-1">
            {links.map((link) => {
              const active = isActive(pathname, link.href);
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "rounded-full px-3.5 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-ink-900 text-white"
                        : "text-ink-600 hover:bg-ink-100 hover:text-ink-900",
                    )}
                  >
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="ml-auto flex items-center gap-2">
          {hydrated && cartCount > 0 ? (
            <ButtonLink
              href="/checkout"
              variant="dark"
              size="sm"
              className="animate-scale-in"
            >
              <ShoppingBag className="size-4" aria-hidden />
              <span className="hidden sm:inline">Cart</span>
              <span className="rounded-full bg-white/20 px-1.5 text-xs font-semibold tabular-nums">
                {cartCount}
              </span>
            </ButtonLink>
          ) : null}

          {!onMerchant && user?.role === "MERCHANT" ? (
            <ButtonLink href="/merchant" variant="secondary" size="sm" className="hidden sm:inline-flex">
              <Store className="size-4" aria-hidden />
              My café
            </ButtonLink>
          ) : null}

          {sessionHydrated && user ? (
            <div className="hidden items-center gap-2 sm:flex">
              <Link
                href="/account"
                aria-current={pathname.startsWith("/account") ? "page" : undefined}
                className={cn(
                  "max-w-40 truncate rounded-full px-2 py-1 text-sm font-medium transition-colors hover:bg-ink-100",
                  pathname.startsWith("/account") ? "text-ink-900" : "text-ink-700",
                )}
              >
                {user.display_name}
              </Link>
              <Button variant="ghost" size="sm" onClick={handleSignOut}>
                <LogOut className="size-4" aria-hidden />
                Sign out
              </Button>
            </div>
          ) : (
            <ButtonLink href="/login" variant="outline" size="sm" className="hidden sm:inline-flex">
              <UserIcon className="size-4" aria-hidden />
              Sign in
            </ButtonLink>
          )}

          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            aria-label="Open menu"
            className="inline-flex size-10 items-center justify-center rounded-full border border-ink-200 bg-white text-ink-700 transition hover:bg-ink-50 md:hidden"
          >
            <Menu className="size-5" aria-hidden />
          </button>
        </div>
      </div>

      <Modal
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
        title="ReadyBy"
        description="Order ahead. It'll be ready when you arrive."
        placement="right"
      >
        <nav aria-label="Mobile">
          <ul className="flex flex-col gap-1">
            {links.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  onClick={() => setMenuOpen(false)}
                  className={cn(
                    "flex items-center justify-between rounded-2xl px-4 py-3.5 text-base font-medium transition-colors",
                    isActive(pathname, link.href)
                      ? "bg-ink-900 text-white"
                      : "text-ink-800 hover:bg-ink-100",
                  )}
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="mt-6 border-t border-ink-100 pt-6">
          {user ? (
            <div className="flex flex-col gap-2.5">
              <p className="text-sm text-ink-500">
                Signed in as{" "}
                <span className="font-medium text-ink-800">{user.display_name}</span>
              </p>
              {user.role === "MERCHANT" ? (
                <ButtonLink
                  href="/merchant"
                  variant="dark"
                  fullWidth
                  onClick={() => setMenuOpen(false)}
                >
                  <Store className="size-4" aria-hidden />
                  My café board
                </ButtonLink>
              ) : null}
              <ButtonLink
                href="/account"
                variant="secondary"
                fullWidth
                onClick={() => setMenuOpen(false)}
              >
                <UserIcon className="size-4" aria-hidden />
                Account settings
              </ButtonLink>
              <Button
                variant="outline"
                fullWidth
                onClick={() => {
                  setMenuOpen(false);
                  void handleSignOut();
                }}
              >
                <LogOut className="size-4" aria-hidden />
                Sign out
              </Button>
            </div>
          ) : (
            <div className="flex flex-col gap-2.5">
              <ButtonLink
                href="/login"
                variant="dark"
                fullWidth
                onClick={() => setMenuOpen(false)}
              >
                <UserIcon className="size-4" aria-hidden />
                Sign in
              </ButtonLink>
              <ButtonLink
                href="/register"
                variant="outline"
                fullWidth
                onClick={() => setMenuOpen(false)}
              >
                Create an account
              </ButtonLink>
            </div>
          )}
        </div>
      </Modal>
    </header>
  );
}