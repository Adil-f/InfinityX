import { NextResponse } from "next/server";
import { db } from "@/lib/db";
export async function GET() {
  return NextResponse.json(db().prepare(`SELECT * FROM audit_logs ORDER BY at DESC LIMIT 200`).all());
}
