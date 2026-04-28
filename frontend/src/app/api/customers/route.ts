import { NextResponse } from "next/server";
import { db, collection, getDocs } from "@/lib/firebase";

interface Customer {
  customer_id: string;
  name: string;
  email: string;
  whatsapp: string;
  address?: string;
  total_spent: number;
  purchase_count: number;
  customer_level: "new" | "standard" | "vip";
  last_purchase_date?: Date;
  created_at: Date;
}

// GET - Fetch all customers
export async function GET() {
  try {
    const snapshot = await getDocs(collection(db, "customers"));

    const customers: Customer[] = [];

    snapshot.forEach((doc) => {
      const data = doc.data();
      customers.push({
        customer_id: doc.id,
        name: data.name || "",
        email: data.email || "",
        whatsapp: data.whatsapp || "",
        address: data.address,
        total_spent: data.total_spent || 0,
        purchase_count: data.purchase_count || 0,
        customer_level: data.customer_level || "new",
        last_purchase_date: data.last_purchase_date?.toDate(),
        created_at: data.created_at?.toDate() || new Date(),
      });
    });

    // Sort by total_spent descending
    customers.sort((a, b) => b.total_spent - a.total_spent);

    return NextResponse.json({ customers });
  } catch (error) {
    console.error("Error fetching customers:", error);
    return NextResponse.json(
      { error: "Failed to fetch customers", customers: [] },
      { status: 500 },
    );
  }
}
