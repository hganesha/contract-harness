import type { Order } from "../types";

// Dummy data seeded during the Lovable build-out.
export const mockOrders: Order[] = [
  {
    id: "ord-1001",
    customerName: "Ada Lovelace",
    customerEmail: "ada@example.com",
    items: [
      { id: "i-1", name: "Mechanical keyboard", price: 120.0, qty: 1 },
      { id: "i-2", name: "USB-C cable", price: 9.99, qty: 2 },
    ],
    status: "pending",
    total: 139.99,
    discountCode: "SAVE10",
    notes: "Leave at front desk",
    createdAt: "2026-10-01T14:22:00Z",
  },
  {
    id: "ord-1002",
    customerName: "Grace Hopper",
    customerEmail: "grace@example.com",
    items: [
      { id: "i-3", name: "Compiler science mug", price: 18.5, qty: 3 },
    ],
    status: "refunded", // not a real status in the backend enum
    total: 55.5,
    notes: null as unknown as string,
  },
  {
    id: "ord-1003",
    customerName: "Alan Turing",
    customerEmail: "alan@example.com",
    items: [
      { id: "i-4", name: "Enigma puzzle set", price: 45.0, qty: 1 },
    ],
    status: "shipped",
    total: 48.71,
    createdAt: "2026-10-18T09:05:00Z",
  },
];
