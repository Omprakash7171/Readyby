import { ButtonLink } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="mx-auto flex w-full max-w-xl flex-col items-center px-5 py-24 text-center sm:py-32">
      <span
        aria-hidden
        className="grid size-16 place-items-center rounded-3xl bg-crema-100 text-3xl font-semibold text-ink-300"
      >
        404
      </span>
      <h1 className="mt-6 text-3xl font-semibold tracking-[-0.035em] text-ink-900">
        We couldn&rsquo;t find that page
      </h1>
      <p className="mt-3 text-pretty text-base text-ink-500">
        Try heading back to the demo and picking a destination.
      </p>
      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <ButtonLink href="/" size="lg">
          Back to ReadyBy
        </ButtonLink>
        <ButtonLink href="/explore" variant="outline" size="lg">
          Find nearby shops
        </ButtonLink>
      </div>
    </div>
  );
}