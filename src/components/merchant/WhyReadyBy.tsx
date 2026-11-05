"use client";

import {
  ArrowRight,
  ClipboardList,
  Footprints,
  Timer,
  Users,
} from "lucide-react";
import { Card, SectionHeading } from "@/components/ui/Card";

/**
 * Written for a café owner hearing the pitch for the first time: what changes
 * in the working day, without promising revenue that cannot be guaranteed.
 */
const reasons = [
  {
    icon: Users,
    title: "Orders from people already nearby",
    body: "Customers within walking distance can order before they set off, so the sale happens on your way past instead of being lost to a bigger chain.",
  },
  {
    icon: Timer,
    title: "Prep timed to the arrival, not the queue",
    body: "Each order says when the customer will walk in, so you know roughly when to start the machine instead of everything landing at once.",
  },
  {
    icon: Footprints,
    title: "Pickup only — no delivery to run",
    body: "No driver, no route, no packaging. Customers come to your counter, which keeps the operation as simple as it is today.",
  },
  {
    icon: ClipboardList,
    title: "Fits the way you already work",
    body: "A single board showing what is new, what is being made and what is waiting, with the arrival time on every ticket.",
  },
];

export function WhyReadyBy() {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-ink-100 px-5 py-5 sm:px-7 sm:py-6">
        <SectionHeading
          align="left"
          className="max-w-none"
          eyebrow="For café owners"
          title={
            <>
              Why <span className="text-brand-600">ReadyBy</span> for your café?
            </>
          }
          description="This isn't just another online order. It tells you when the customer is walking over, so you can start the right thing at the right time."
        />
      </div>

      <ul className="grid gap-px bg-ink-100 sm:grid-cols-2">
        {reasons.map((reason) => {
          const Icon = reason.icon;
          return (
            <li key={reason.title} className="bg-white px-5 py-6 sm:px-7 sm:py-7">
              <span
                aria-hidden
                className="grid size-10 place-items-center rounded-2xl bg-brand-50 text-brand-600"
              >
                <Icon className="size-5" />
              </span>
              <h3 className="mt-4 text-[1.02rem] font-semibold tracking-[-0.02em] text-ink-900">
                {reason.title}
              </h3>
              <p className="mt-1.5 text-pretty text-sm leading-relaxed text-ink-500">
                {reason.body}
              </p>
            </li>
          );
        })}
      </ul>

      <div className="border-t border-ink-100 bg-white px-5 py-5 sm:px-7">
        <p className="flex items-start gap-2 text-pretty text-sm leading-relaxed text-ink-500">
          <ArrowRight className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden />
          <span>
            Your board shows real pickup sales for the day as you take orders, not
            a forecast. Every ticket carries the customer&rsquo;s arrival time, so
            prep starts when it should.
          </span>
        </p>
      </div>
    </Card>
  );
}
