import { cookies } from "next/headers";

const COOKIE = "ix_owner";

export function expectedSecret(): string {
  return process.env.AGENCY_OWNER_SECRET || "change-me-local-only";
}

export async function isOwnerAuthenticated(): Promise<boolean> {
  const jar = await cookies();
  return jar.get(COOKIE)?.value === expectedSecret();
}

export function ownerCookieHeader(secret: string): string {
  return `${COOKIE}=${encodeURIComponent(secret)}; Path=/; HttpOnly; SameSite=Lax`;
}
