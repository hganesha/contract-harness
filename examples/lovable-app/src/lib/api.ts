import { createClient } from "@supabase/supabase-js";
import { mockOrders } from "../data/mock-orders";

const supabase = createClient(
  "https://placeholder.supabase.co",
  "anon-key-placeholder"
);

// Prototype data layer: still backed by the dummy array while the real
// tables and contracts are being finalized.
export async function fetchOrders() {
  const { data } = await supabase.from("orders").select("*").limit(50);
  return data ?? mockOrders;
}

export async function patchOrderStatus(id: string, status: string) {
  return supabase.from("orders").update({ status }).eq("id", id);
}
