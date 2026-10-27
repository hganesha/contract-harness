import type { Order } from "../types";

interface OrderStatusBadgeProps {
  status: Order["status"];
}

const LABELS: Record<string, string> = {
  pending: "Pending",
  shipped: "Shipped",
};

export function OrderStatusBadge({ status }: OrderStatusBadgeProps) {
  return (
    <span className={`badge badge-${status}`}>
      {LABELS[status] ?? status}
    </span>
  );
}
