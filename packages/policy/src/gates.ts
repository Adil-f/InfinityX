import { ApprovalAction, ApprovalStatus, PolicyBlockedError } from "../../core/src/index";

export function assertApproved(
  action: ApprovalAction,
  status: ApprovalStatus | null | undefined,
): void {
  if (status !== "approved") {
    throw new PolicyBlockedError(
      `Action "${action}" blocked: requires approved ApprovalRequest (got ${status ?? "none"}).`,
    );
  }
}

export function canSendEmail(status: ApprovalStatus | null | undefined): boolean {
  return status === "approved";
}

export function canPublishSite(status: ApprovalStatus | null | undefined): boolean {
  return status === "approved";
}

export function canSpend(status: ApprovalStatus | null | undefined): boolean {
  return status === "approved";
}

/** Phase 2: transport is never wired even if approved. */
export function sendEmailTransportAvailable(): boolean {
  return false;
}

export function publishTransportAvailable(): boolean {
  return false;
}
