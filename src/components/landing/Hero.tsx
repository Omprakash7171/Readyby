import {
  ArrowRight,
  CheckCircle2,
  Clock,
  MapPin,
  Sparkles,
} from "lucide-react";
import { ButtonAnchor, ButtonLink } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { FoodArt } from "@/components/ui/FoodArt";
import { AuthChoices } from "@/components/landing/AuthChoices";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <BackdropGlow />

      <div className="mx-auto grid w-full max-w-6xl items-center gap-12 px-5 pt-14 pb-10 sm:pt-20 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pt-24 lg:pb-14">
        <div className="animate-fade-up">
          <Badge tone="brand" className="mb-6">
            <Sparkles className="size-3.5" aria-hidden />
            Pickup only · No delivery
          </Badge>

          <h1 className="text-balance text-[2.6rem] leading-[1.03] font-semibold tracking-[-0.04em] text-ink-900 sm:text-6xl lg:text-[4.1rem]">
            Order ahead.
            <br />
            It&rsquo;ll be ready
            <br />
            when you arrive.
          </h1>

          <p className="mt-6 max-w-xl text-pretty text-lg leading-relaxed text-ink-500 sm:text-xl">
            Tell a nearby café when you&rsquo;ll arrive and they&rsquo;ll have it
            ready the moment you walk in. Skip the queue and go straight to the
            counter.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <ButtonLink href="/explore" size="lg">
              Find nearby shops
              <ArrowRight className="size-4.5" aria-hidden />
            </ButtonLink>
            <ButtonAnchor href="#how-it-works" variant="outline" size="lg">
              <Clock className="size-4.5" aria-hidden />
              See how it works
            </ButtonAnchor>
          </div>

          <ul className="mt-9 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink-500">
            <li className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="size-4 text-ready-500" aria-hidden />
              No queue
            </li>
            <li className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="size-4 text-ready-500" aria-hidden />
              No delivery
            </li>
            <li className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="size-4 text-ready-500" aria-hidden />
              No card needed
            </li>
          </ul>
        </div>

        <HeroVisual />
      </div>

      {/**
       * Full width beneath the hero so both panels get room to sit side by side,
       * and so the two audiences read as equals rather than the café being a
       * footnote under the customer's call to action.
       */}
      <div className="mx-auto w-full max-w-6xl px-5 pb-16 sm:pb-24">
        <AuthChoices />
      </div>
    </section>
  );
}

function BackdropGlow() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
      <div className="absolute top-[-18rem] left-1/2 size-[46rem] -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_center,rgba(225,85,46,0.14),transparent_62%)] blur-2xl" />
      <div className="absolute top-24 right-[-14rem] size-[34rem] rounded-full bg-[radial-gradient(circle_at_center,rgba(16,185,129,0.12),transparent_65%)] blur-2xl" />
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(22,18,15,0.045) 1px, transparent 1px), linear-gradient(to bottom, rgba(22,18,15,0.045) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          maskImage:
            "radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%)",
        }}
      />
    </div>
  );
}

const arrivalSlots = ["10:00 AM", "10:15 AM", "10:30 AM", "10:45 AM"];

function HeroVisual() {
  return (
    <div className="relative mx-auto w-full max-w-sm lg:max-w-none">
      <div
        aria-hidden
        className="absolute -inset-6 -z-10 rounded-[3rem] bg-gradient-to-br from-brand-100/70 via-transparent to-ready-100/70 blur-2xl"
      />

      <div className="animate-fade-up rounded-[2.5rem] border border-ink-900/8 bg-white/85 p-3 shadow-pop backdrop-blur-sm [animation-delay:120ms]">
        <div className="overflow-hidden rounded-[2rem] border border-ink-100 bg-crema-50">
          <div className="flex items-center gap-2 border-b border-ink-100 bg-white px-4 py-3">
            <span className="size-2.5 rounded-full bg-ink-200" />
            <span className="size-2.5 rounded-full bg-ink-200" />
            <span className="size-2.5 rounded-full bg-ink-200" />
            <span className="ml-2 text-xs font-medium text-ink-400">
              readyby.app/explore
            </span>
          </div>

          <div className="px-4 py-5">
            <p className="text-[0.7rem] font-semibold tracking-[0.16em] text-brand-600 uppercase">
              Destination
            </p>
            <p className="mt-1 text-lg font-semibold tracking-[-0.02em] text-ink-900">
              City Centre Salon
            </p>

            <div className="mt-4 flex items-center gap-3 rounded-2xl border border-ink-100 bg-white p-3">
              <FoodArt
                variant="latte"
                className="size-11 shrink-0 rounded-xl ring-1 ring-ink-900/5"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-ink-900">
                  Bean & Brew
                </p>
                <p className="text-xs text-ink-500">2 min walk · 4.8 ★</p>
              </div>
              <span className="rounded-full bg-ready-50 px-2 py-0.5 text-[0.65rem] font-semibold text-ready-700">
                Open
              </span>
            </div>

            <p className="mt-5 text-[0.7rem] font-semibold tracking-[0.16em] text-brand-600 uppercase">
              Arrival time
            </p>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {arrivalSlots.map((slot, index) => (
                <span
                  key={slot}
                  className={
                    index === 1
                      ? "rounded-xl border border-brand-400 bg-brand-50 px-3 py-2 text-center text-sm font-semibold text-brand-700"
                      : "rounded-xl border border-ink-200 bg-white px-3 py-2 text-center text-sm font-medium text-ink-700"
                  }
                >
                  {slot}
                </span>
              ))}
            </div>
            <p className="mt-3 rounded-xl bg-brand-50 px-3 py-2 text-xs font-medium text-brand-800">
              Ready by 10:15 AM
            </p>
          </div>
        </div>
      </div>

      <div className="animate-float-slow absolute -right-3 -bottom-5 flex items-center gap-3 rounded-2xl border border-ink-100 bg-white px-4 py-3 shadow-lift sm:-right-8">
        <span className="grid size-9 place-items-center rounded-xl bg-ready-50 text-ready-600">
          <CheckCircle2 className="size-5" aria-hidden />
        </span>
        <span>
          <span className="block text-sm font-semibold text-ink-900">
            Ready for pickup
          </span>
          <span className="block text-xs text-ink-500">
            10:15 AM · Order #RB1024
          </span>
        </span>
      </div>

      <div className="animate-float-slow absolute -top-4 -left-4 hidden items-center gap-2 rounded-2xl border border-ink-100 bg-white px-3.5 py-2.5 shadow-lift sm:flex [animation-delay:1.4s]">
        <MapPin className="size-4 text-brand-500" aria-hidden />
        <span className="text-xs font-medium text-ink-700">
          5 shops within 10 min walk
        </span>
      </div>
    </div>
  );
}