export type LeadStatus = "new" | "qualified" | "contact_pending" | "won" | "lost";
export type DraftChannel = "email" | "whatsapp" | "other";
export type DraftStatus = "draft" | "awaiting_approval" | "approved" | "rejected" | "sent_externally_manual";
export type ApprovalAction =
  | "send_email"
  | "publish_site"
  | "spend"
  | "domain"
  | "crm_export"
  | "enable_form_submit"
  | "other";
export type ApprovalStatus = "pending" | "approved" | "rejected";
export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "blocked";

export const LAYOUT_FAMILIES = [
  "ristorante-editorial",
  "negozio-catalog",
  "artigiano-workshop",
  "studio-professional",
  "servizi-local",
  "hospitality-welcome",
] as const;
export type LayoutFamily = (typeof LAYOUT_FAMILIES)[number];

export class PolicyBlockedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PolicyBlockedError";
  }
}
