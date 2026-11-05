import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "@/context/SessionProvider";
import { BookingProvider } from "@/context/BookingProvider";
import { AppChrome } from "@/components/layout/AppChrome";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "ReadyBy — Order ahead. It'll be ready when you arrive.",
    template: "%s · ReadyBy",
  },
  description:
    "Order from nearby cafés and shops before you get there. Skip the queue and pick up when it's ready.",
  applicationName: "ReadyBy",
  keywords: ["ReadyBy", "order ahead", "pickup", "coffee", "café", "demo"],
};

export const viewport: Viewport = {
  themeColor: "#fdfaf6",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-GB">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-100 focus:rounded-full focus:bg-ink-900 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to content
        </a>
        <SessionProvider>
          <BookingProvider>
            <AppChrome>{children}</AppChrome>
          </BookingProvider>
        </SessionProvider>
      </body>
    </html>
  );
}