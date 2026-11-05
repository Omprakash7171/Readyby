import { Coffee, ShoppingBag } from "lucide-react";
import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

/**
 * The two doors into ReadyBy, side by side.
 *
 * A customer orders and follows a pickup, so they get both a sign-in and a
 * sign-up. A café runs the pickup board, so it gets a sign-in only: merchant
 * accounts are opened by the ReadyBy team rather than by whoever fills in a
 * form, which is why there is deliberately no café sign-up here.
 *
 * The café button carries `next`, so signing in lands on the board instead of
 * the default destination page. That parameter is echoed back through
 * /login and /register untouched, so a café arriving from a link keeps its
 * destination.
 */
export function AuthChoices() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Card className="flex flex-col p-6">
        <PanelHeading
          icon={<ShoppingBag className="size-5" aria-hidden />}
          eyebrow="For customers"
          title="Order ahead, skip the queue"
        />
        <p className="mt-4 text-sm leading-relaxed text-ink-500">
          Create an account to place an order and follow it through to the
          counter. Or sign in if you already have one.
        </p>
        <div className="mt-6 flex flex-wrap gap-2.5">
          <ButtonLink href="/login" variant="dark" size="md">
            Sign in
          </ButtonLink>
          <ButtonLink href="/register" variant="outline" size="md">
            Create account
          </ButtonLink>
        </div>
      </Card>

      <Card className="flex flex-col p-6">
        <PanelHeading
          icon={<Coffee className="size-5" aria-hidden />}
          eyebrow="For cafés"
          title="Start each order on time"
        />
        <p className="mt-4 text-sm leading-relaxed text-ink-500">
          Every ticket shows the time the customer is walking in, so the right
          thing starts at the right moment.
        </p>
        <div className="mt-6 flex flex-wrap gap-2.5">
          <ButtonLink href="/login?next=%2Fmerchant" variant="dark" size="md">
            <Coffee className="size-4" aria-hidden />
            Café sign in
          </ButtonLink>
        </div>
        <p className="mt-4 text-xs leading-relaxed text-ink-400">
          Café accounts are opened by the ReadyBy team. Ask your contact to set
          yours up, then sign in here.
        </p>
      </Card>
    </div>
  );
}

function PanelHeading({
  icon,
  eyebrow,
  title,
}: {
  icon: React.ReactNode;
  eyebrow: string;
  title: string;
}) {
  return (
    <div className="flex items-start gap-3.5">
      <span className="grid size-10 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600">
        {icon}
      </span>
      <div>
        <p className="text-xs font-semibold tracking-[0.18em] text-brand-600 uppercase">
          {eyebrow}
        </p>
        <h2 className="mt-1 text-lg font-semibold tracking-[-0.02em] text-ink-900">
          {title}
        </h2>
      </div>
    </div>
  );
}
