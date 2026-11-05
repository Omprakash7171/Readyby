"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useSession } from "@/context/SessionProvider";
import { customerDestination } from "@/lib/redirects";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

/** Signed-in café owners only use the café workspace and their account page. */
function isOwnerRoute(pathname: string) {
  return pathname === "/account" || pathname === "/merchant" || pathname.startsWith("/merchant/");
}

/**
 * The customer-facing frame (navbar and footer). It is deliberately absent from
 * the café workspace, and from every page for a signed-in café owner: an owner
 * who lands on the homepage, sign-in or any customer page is sent straight back
 * to their dashboard instead.
 */
export function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, hydrated } = useSession();

  const inCafeWorkspace = pathname === "/merchant" || pathname.startsWith("/merchant/");
  const isCafeOwner = hydrated && user?.role === "MERCHANT";
  const signedIn = hydrated && user !== null;
  const onAuthPage = pathname === "/login" || pathname === "/register";

  // Owners live in the café workspace; everyone else who is already signed in
  // has no reason to see the sign-in or registration form again.
  const redirectTo =
    isCafeOwner && !isOwnerRoute(pathname)
      ? "/merchant"
      : signedIn && !isCafeOwner && onAuthPage
        ? "/explore"
        : null;
  const blocked = redirectTo !== null;

  useEffect(() => {
    if (!redirectTo) return;
    // Honour a `next` deep link when bouncing a signed-in customer off the
    // auth pages, otherwise send them to the storefront.
    if (onAuthPage && redirectTo === "/explore") {
      const requested = new URLSearchParams(window.location.search).get("next");
      router.replace(customerDestination(requested));
      return;
    }
    router.replace(redirectTo);
  }, [redirectTo, onAuthPage, router]);

  const hideChrome = inCafeWorkspace || isCafeOwner;

  return (
    <div className="flex min-h-dvh flex-col">
      {hideChrome ? null : <Navbar />}
      <main id="main" className="flex-1">
        {blocked ? null : children}
      </main>
      {hideChrome ? null : <Footer />}
    </div>
  );
}
