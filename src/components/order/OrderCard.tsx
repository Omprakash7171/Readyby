import Link from "next/link";
import { Clock, MapPin } from "lucide-react";
import type { ApiOrderSummaryRow } from "@/lib/apiTypes";
import { formatPrice } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { FoodArt } from "@/components/ui/FoodArt";
import { OrderStatusBadge } from "@/components/order/OrderStatus";

export function OrderCard({ order }: { order: ApiOrderSummaryRow }) {
  const items = order.items.join(" · ");

  return (
    <Card as="li" interactive className="overflow-hidden">
      <Link
        href={`/orders/${order.public_id}`}
        className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:p-5"
        aria-label={`View order ${order.public_id} from ${order.cafe.name}`}
      >
        <div className="flex items-center gap-3 sm:w-44 sm:shrink-0">
          <FoodArt
            variant={order.items_detailed[0]?.art ?? "hot-cup"}
            className="size-12 shrink-0 rounded-2xl ring-1 ring-ink-900/5"
          />
          <div className="min-w-0">
            <p className="font-mono text-sm font-semibold text-ink-900">
              {order.public_id}
            </p>
            <p className="truncate text-sm text-ink-500">{order.cafe.name}</p>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm text-ink-600">{items}</p>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-500">
            <span className="inline-flex items-center gap-1.5 font-medium text-brand-700">
              <Clock className="size-3.5 text-brand-500" aria-hidden />
              Ready by {order.estimated_ready_time_label}
            </span>
            {order.destination_label ? (
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="size-3.5 text-ink-400" aria-hidden />
                {order.destination_label}
              </span>
            ) : null}
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 sm:justify-end">
          <OrderStatusBadge status={order.status} label={order.status_label} />
          <span className="text-sm font-semibold text-ink-900 tabular-nums">
            {formatPrice(Number(order.subtotal))}
          </span>
        </div>
      </Link>
    </Card>
  );
}