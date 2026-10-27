import { mockOrders } from "../data/mock-orders";
import { OrderStatusBadge } from "./OrderStatusBadge";
import { OrderSummary } from "./OrderSummary";
import type { StatusFilter } from "../types";

interface OrderListProps {
  filter: StatusFilter;
}

export function OrderList({ filter }: OrderListProps) {
  const orders =
    filter === "all" ? mockOrders : mockOrders.filter((o) => o.status === filter);

  return (
    <ul className="order-list">
      {orders.map((order) => (
        <li key={order.id} className="order-card">
          <header>
            <strong>{order.id}</strong>
            <OrderStatusBadge status={order.status} />
          </header>
          <p>{order.customerName} — {order.customerEmail}</p>
          <ul>
            {order.items.map((item) => (
              <li key={item.id}>
                {item.name} × {item.qty} @ ${item.price}
              </li>
            ))}
          </ul>
          <OrderSummary order={order} />
          <small>Placed: {order.createdAt}</small>
        </li>
      ))}
    </ul>
  );
}
