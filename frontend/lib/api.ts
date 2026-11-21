export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Finding = {
  id?: string;
  entity_type: string;
  value: string;
  normalized_value: string;
  title: string;
  summary: string;
  source_id: string;
  source_name: string;
  source_url?: string | null;
  collected_at?: string | null;
  confidence: number;
  verified: boolean;
  kind: string;
  attributes?: Record<string, unknown>;
  is_fixture?: boolean;
};

export type SearchResponse = {
  job_id: string | null;
  query_type: string;
  normalized_query?: string;
  status: string;
  credits_charged: number;
  credits_remaining: number;
  findings: Finding[];
  unavailable: { source_id: string; source_name?: string; message: string; required_env?: string[] }[];
  errors: { source_id?: string; message: string; suggested_module?: string }[];
  notes: string[];
  suggested_module?: string | null;
  options?: string[];
  provider_response?: { stored_at_rest: boolean; payload: unknown; note: string };
};

export type Me = {
  id: string | null;
  email: string | null;
  full_name: string;
  role: string;
  org_name: string;
  plan: string;
  credits_balance: number;
  mfa_enabled: boolean;
  is_fixture: boolean;
  organization_is_fixture: boolean;
  permissions: string[];
};

export function messageFrom(body: unknown, status: number) {
  if (!body || typeof body !== "object") return `Request failed (${status})`;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => (item as { msg?: string }).msg || "Invalid input").join("; ");
  return `Request failed (${status})`;
}

export async function api<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  const text = await response.text();
  const body = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const error = new Error(messageFrom(body, response.status));
    (error as Error & { status: number }).status = response.status;
    throw error;
  }
  return body as T;
}
