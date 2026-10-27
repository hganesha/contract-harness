import type { Order } from "../types";

interface OrderSummaryProps {
  order: Order;
}

export function OrderSummary({ order }: OrderSummaryProps) {
  const itemCount = order.items.reduce((sum, item) => sum + item.qty, 0);
  return (
    <div className="order-summary">
      <p>Items: {itemCount}</p>
      <p>Discount code: {order.discountCode ?? "—"}</p>
      <p>Total: ${order.total.toFixed(2)}</p>
      {order.notes && <p className="notes">{order.notes}</p>}
    </div>
  );
}
