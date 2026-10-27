// Types generated ad-hoc inside Lovable while prototyping with dummy data.
export interface OrderItem {
  id: string;
  name: string;
  price: number;
  qty: number;
}

export interface Order {
  id: string;
  customerName: string;
  customerEmail: string;
  items: OrderItem[];
  status: string;
  total: number;
  discountCode?: string;
  notes?: string;
  createdAt: string;
}

export type StatusFilter = "all" | "pending" | "shipped";
