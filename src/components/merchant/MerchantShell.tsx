"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ClipboardList,
  Clock3,
  LayoutDashboard,
  LogOut,
  Settings,
  UserRound,
  UtensilsCrossed,
} from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/format";
import { useSession } from "@/context/SessionProvider";

const NAV = [
  { href: "/merchant", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/merchant/orders", label: "Orders", icon: ClipboardList },
  { href: "/merchant/menu", label: "Menu", icon: UtensilsCrossed },
  { href: "/merchant/pickup-slots", label: "Pickup slots", icon: Clock3 },
  { href: "/merchant/settings", label: "Cafe settings", icon: Settings },
];

export function MerchantShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut } = useSession();

  async function handleSignOut() {
    await signOut();
    router.replace("/login");
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-5 py-6 sm:py-8 lg:flex-row lg:items-start lg:gap-10">
      <aside className="lg:sticky lg:top-24 lg:w-56 lg:shrink-0">
        <p className="px-3 text-xs font-semibold tracking-[0.16em] text-ink-400 uppercase">
          Cafe workspace
        </p>
        <nav aria-label="Cafe workspace" className="mt-3">
          <ul className="no-scrollbar flex gap-1.5 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible">
            {NAV.map((item) => {
              const active = item.exact
                ? pathname === item.href
                : pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <li key={item.href} className="shrink-0">
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-2.5 rounded-2xl px-3.5 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-ink-900 text-white shadow-soft"
                        : "text-ink-600 hover:bg-white hover:text-ink-900",
                    )}
                  >
                    <Icon className="size-4" aria-hidden />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="mt-4 rounded-2xl border border-ink-100 bg-white p-3.5">
          <p className="px-1 text-xs text-ink-400">Signed in as</p>
          <p className="mt-0.5 truncate px-1 text-sm font-medium text-ink-800">
            {user?.display_name ?? "Café owner"}
          </p>
          <Link
            href="/account"
            className="mt-3 flex items-center gap-2 rounded-xl px-2 py-1.5 text-sm font-medium text-ink-600 transition hover:bg-ink-100 hover:text-ink-900"
          >
            <UserRound className="size-4" aria-hidden />
            Account settings
          </Link>
          <button
            type="button"
            onClick={() => void handleSignOut()}
            className="mt-0.5 flex w-full items-center gap-2 rounded-xl px-2 py-1.5 text-sm font-medium text-ink-600 transition hover:bg-ink-100 hover:text-ink-900"
          >
            <LogOut className="size-4" aria-hidden />
            Sign out
          </button>
        </div>
      </aside>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
