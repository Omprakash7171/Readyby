import {
  ArrowRight,
  ClipboardList,
  Coffee,
  Footprints,
  MapPin,
  PackageCheck,
  Timer,
} from "lucide-react";
import { Section, SectionHeading, Card } from "@/components/ui/Card";
import { ButtonLink } from "@/components/ui/Button";

const steps = [
  {
    icon: MapPin,
    step: "01",
    title: "Destination",
    body: "You're heading to the salon, the gym, the office, uni or the station.",
  },
  {
    icon: Footprints,
    step: "02",
    title: "Arrival time",
    body: "Pick roughly when you'll walk in. That's the time everything else works back from.",
  },
  {
    icon: ClipboardList,
    step: "03",
    title: "Order",
    body: "Choose a nearby café and add what you want. Every café shows what it can have ready.",
  },
  {
    icon: Timer,
    step: "04",
    title: "Prepared",
    body: "The café starts a few minutes before you arrive so it lands as you do.",
  },
  {
    icon: PackageCheck,
    step: "05",
    title: "Pickup",
    body: "Walk in, say your order number, take your coffee and go.",
  },
];

export function HowItWorks() {
  return (
    <Section id="how-it-works" className="bg-white">
      <SectionHeading
        eyebrow="How it works"
        title="Destination → Arrival time → Order → Prepared → Pickup"
        description="The arrival time is the important part. Once the customer knows when they'll be there, the café knows when to start."
      />

      <ol className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {steps.map((item, index) => {
          const Icon = item.icon;
          return (
            <li key={item.title} className="relative">
              <Card
                interactive
                className="group h-full overflow-hidden p-6"
              >
                <span
                  aria-hidden
                  className="absolute top-4 right-5 font-mono text-4xl font-semibold text-ink-100 transition-colors duration-300 group-hover:text-brand-100"
                >
                  {item.step}
                </span>
                <span className="relative grid size-11 place-items-center rounded-2xl bg-ink-900 text-white transition-colors duration-300 group-hover:bg-brand-500">
                  <Icon className="size-5" />
                </span>
                <h3 className="relative mt-5 text-lg font-semibold tracking-[-0.02em] text-ink-900">
                  {item.title}
                </h3>
                <p className="relative mt-2 text-pretty text-sm leading-relaxed text-ink-500">
                  {item.body}
                </p>
              </Card>

              {index < steps.length - 1 ? (
                <span
                  aria-hidden
                  className="absolute top-1/2 -right-2.5 hidden size-6 -translate-y-1/2 place-items-center rounded-full border border-ink-100 bg-white text-ink-300 lg:grid"
                >
                  <ArrowRight className="size-3.5" />
                </span>
              ) : null}
            </li>
          );
        })}
      </ol>
    </Section>
  );
}

const benefits = [
  {
    title: "Skip the queue",
    body: "Order before you arrive.",
    detail:
      "The counter is already busy. Put your order in while you're still walking and it joins the queue as a prepared order, not a walk-up one.",
  },
  {
    title: "Ready when you arrive",
    body: "Choose a pickup time that fits your journey.",
    detail:
      "Appointment at 10:00? Pick 10:15. The café starts your drink at the right moment instead of the moment you happen to walk in.",
  },
  {
    title: "Simple pickup",
    body: "Walk in, collect your order, and go.",
    detail:
      "One order number, one counter, no delivery drivers, no waiting room. You're gone in under a minute.",
  },
];

export function Benefits() {
  return (
    <Section>
      <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16">
        <div className="lg:sticky lg:top-24 lg:self-start">
          <SectionHeading
            align="left"
            eyebrow="Why ReadyBy"
            title={
              <>
                Your customers are
                <br />
                already coming here.
              </>
            }
            description="ReadyBy doesn't ask people to change their routine. It fits inside the journey they were already on."
          />
          <ButtonLink href="/explore" className="mt-8" size="lg">
            Find nearby shops
            <ArrowRight className="size-4.5" aria-hidden />
          </ButtonLink>
        </div>

        <ul className="space-y-4">
          {benefits.map((benefit, index) => (
            <li key={benefit.title}>
              <Card
                as="article"
                interactive
                className="flex gap-5 p-6 sm:p-7"
              >
                <span
                  aria-hidden
                  className="grid size-10 shrink-0 place-items-center rounded-2xl bg-brand-50 font-mono text-sm font-semibold text-brand-600"
                >
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="text-lg font-semibold tracking-[-0.02em] text-ink-900">
                    {benefit.title}
                  </h3>
                  <p className="mt-0.5 font-medium text-brand-600">
                    {benefit.body}
                  </p>
                  <p className="mt-2.5 text-pretty text-sm leading-relaxed text-ink-500">
                    {benefit.detail}
                  </p>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

const audiences = [
  "the salon",
  "the gym",
  "the office",
  "university",
  "the station",
];

export function UseCase() {
  return (
    <Section className="bg-ink-900 text-white">
      <div className="grid gap-10 lg:grid-cols-[1fr_0.9fr] lg:items-center lg:gap-16">
        <div>
          <p className="text-xs font-semibold tracking-[0.18em] text-brand-300 uppercase">
            The use case
          </p>
          <p className="mt-5 text-balance text-2xl leading-snug font-medium tracking-[-0.025em] text-pretty sm:text-3xl lg:text-[2.15rem] lg:leading-[1.25]">
            You&rsquo;re heading to{" "}
            <span className="text-brand-300">{audiences.join(", ")}</span>.
            ReadyBy helps you order something nearby before you arrive.
          </p>
        </div>

        <ul className="grid gap-3">
          {[
            {
              who: "Customer",
              line: "I'm already going there.",
              tone: "bg-white/8 text-white",
            },
            {
              who: "ReadyBy",
              line: "Order it before you arrive.",
              tone: "bg-brand-500 text-white",
            },
            {
              who: "Café",
              line: "Prepare it for that time.",
              tone: "bg-white/8 text-white",
            },
            {
              who: "Customer",
              line: "Arrive → collect → leave.",
              tone: "bg-ready-500 text-white",
            },
          ].map((row, index) => (
            <li
              key={row.who + index}
              className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm"
            >
              <span className="w-20 shrink-0 text-xs font-semibold tracking-[0.12em] text-white/50 uppercase">
                {row.who}
              </span>
              <span
                className={`inline-flex rounded-xl px-3 py-1.5 text-sm font-medium ${row.tone}`}
              >
                {row.line}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}

/**
 * The half of the story the customer pages cannot tell. Leads straight to the
 * café demo so a prospective owner can see their own side of the order.
 */
export function ForCafes() {
  return (
    <Section className="bg-white">
      <div className="grid gap-12 lg:grid-cols-[1fr_1fr] lg:items-center lg:gap-16">
        <div>
          <SectionHeading
            align="left"
            eyebrow="For café owners"
            title={
              <>
                Not just another
                <br />
                online order.
              </>
            }
            description="Most online ordering tells you what was ordered. ReadyBy also tells you when the customer is walking through the door — so you can start the right thing at the right time."
          />

          <ul className="mt-8 space-y-4">
            {[
              {
                icon: Footprints,
                title: "The arrival time is on every ticket",
                body: "Not an estimated delivery window. The time the customer said they'd be there.",
              },
              {
                icon: Timer,
                title: "You see when to start",
                body: "A 7 minute drink for a 10:15 AM arrival means starting around 10:08 AM.",
              },
              {
                icon: Coffee,
                title: "Pickup only, no delivery operation",
                body: "No drivers, no routes, no packaging. Customers come to your counter.",
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.title} className="flex gap-4">
                  <span
                    aria-hidden
                    className="grid size-10 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600"
                  >
                    <Icon className="size-5" />
                  </span>
                  <div>
                    <h3 className="font-semibold tracking-[-0.02em] text-ink-900">
                      {item.title}
                    </h3>
                    <p className="mt-1 text-pretty text-sm leading-relaxed text-ink-500">
                      {item.body}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <ButtonLink href="/merchant" size="lg">
              <Coffee className="size-4.5" aria-hidden />
              View the café demo
            </ButtonLink>
            <ButtonLink href="/explore" variant="outline" size="lg">
              Place a customer order
              <ArrowRight className="size-4.5" aria-hidden />
            </ButtonLink>
          </div>
          <p className="mt-4 text-xs text-ink-400">
            Prototype with sample data — the café board is live, the figures are
            illustrative.
          </p>
        </div>

        {/**
         * A static taste of the café board. Real numbers come from the demo
         * page; this is here so the landing page shows the product, not a
         * screenshot description of it.
         */}
        <div className="overflow-hidden rounded-[1.75rem] border border-ink-100 bg-crema-50 shadow-lift">
          <div className="flex items-center justify-between gap-3 border-b border-ink-100 bg-white px-5 py-4">
            <div>
              <p className="text-sm font-semibold text-ink-900">Bean &amp; Brew</p>
              <p className="text-xs text-ink-500">
                Today&rsquo;s pickup orders
              </p>
            </div>
            <span className="rounded-full bg-crema-100 px-2.5 py-1 text-[0.65rem] font-semibold tracking-[0.08em] text-ink-500 uppercase ring-1 ring-ink-200 ring-inset">
              Sample data
            </span>
          </div>

          <ul className="divide-y divide-ink-100">
            {[
              {
                number: "RB-1024",
                items: "Latte, Croissant",
                arrival: "10:15 AM",
                start: "10:08 AM",
                state: "New order",
                tone: "bg-brand-500",
                onTheWay: false,
              },
              {
                number: "RB-1023",
                items: "Flat White, Latte",
                arrival: "10:20 AM",
                start: "10:14 AM",
                state: "Preparing",
                tone: "bg-brand-100",
                onTheWay: true,
              },
              {
                number: "RB-1021",
                items: "Hot chocolate, Croissant",
                arrival: "10:25 AM",
                start: "10:20 AM",
                state: "Ready",
                tone: "bg-ready-500",
                onTheWay: false,
              },
            ].map((ticket) => (
              <li key={ticket.number} className="bg-white px-5 py-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-mono text-sm font-semibold text-ink-900">
                    {ticket.number}
                  </span>
                  <span className="inline-flex items-center gap-1.5 text-xs font-medium text-ink-600">
                    <span
                      aria-hidden
                      className={`size-1.5 rounded-full ${ticket.tone}`}
                    />
                    {ticket.state}
                  </span>
                </div>
                <p className="mt-1 text-sm text-ink-500">{ticket.items}</p>
                <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
                  <span className="font-semibold text-brand-700">
                    Arrives {ticket.arrival}
                  </span>
                  <span className="text-ink-500">Start {ticket.start}</span>
                </div>
                {ticket.onTheWay ? (
                  <p className="mt-2 rounded-xl bg-ready-50 px-2.5 py-1.5 text-xs font-medium text-ready-800">
                    Customer is on the way · simulated estimate
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Section>
  );
}

export function FinalCta() {
  return (
    <Section>
      <div className="relative overflow-hidden rounded-[2rem] border border-brand-200 bg-gradient-to-br from-brand-50 via-crema-50 to-ready-50 px-6 py-14 text-center sm:px-12 sm:py-20">
        <div
          aria-hidden
          className="pointer-events-none absolute -top-24 left-1/2 size-[36rem] -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_center,rgba(225,85,46,0.18),transparent_65%)] blur-2xl"
        />
        <div className="relative">
          <p className="text-balance text-3xl font-semibold tracking-[-0.035em] text-ink-900 sm:text-4xl">
            Ready when you arrive.
          </p>
          <p className="mx-auto mt-4 max-w-lg text-pretty text-base text-ink-500 sm:text-lg">
            Pick a destination, choose when you&rsquo;ll arrive, and see what&rsquo;s
            ready on your way.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <ButtonLink href="/explore" size="lg">
              Find nearby shops
              <ArrowRight className="size-4.5" aria-hidden />
            </ButtonLink>
            <ButtonLink href="/merchant" variant="outline" size="lg">
              <Coffee className="size-4.5" aria-hidden />
              View the café demo
            </ButtonLink>
          </div>
          <p className="mt-6 text-xs text-ink-400">
            Demo checkout · no payment details required
          </p>
        </div>
      </div>
    </Section>
  );
}