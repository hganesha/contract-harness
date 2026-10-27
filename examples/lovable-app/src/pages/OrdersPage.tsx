import { useState } from "react";
import { OrderList } from "../components/OrderList";
import type { StatusFilter } from "../types";

export default function OrdersPage() {
  const [filter, setFilter] = useState<StatusFilter>("all");

  return (
    <main>
      <h1>Orders</h1>
      <select value={filter} onChange={(e) => setFilter(e.target.value as StatusFilter)}>
        <option value="all">All</option>
        <option value="pending">Pending</option>
        <option value="shipped">Shipped</option>
      </select>
      <OrderList filter={filter} />
    </main>
  );
}
