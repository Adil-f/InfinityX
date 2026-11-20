import { NextResponse } from "next/server";
import { db } from "@/lib/db";
export async function GET(_: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const job = db().prepare(`SELECT * FROM jobs WHERE id=?`).get(id);
  if (!job) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json(job);
}
