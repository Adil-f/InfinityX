import { NextResponse } from "next/server";
import { db } from "@/lib/db";
export async function GET() {
  return NextResponse.json(db().prepare(`SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100`).all());
}
