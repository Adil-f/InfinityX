import { PolicyBlockedError } from "../../core/src/index";
import { assertApproved, sendEmailTransportAvailable } from "../../policy/src/gates";
import type { ApprovalStatus } from "../../core/src/index";

export async function createDraftLocal(_input: { to: string; subject: string; body: string }) {
  return { ok: true as const, mode: "local_db_only" as const };
}

export async function sendEmail(_input: {
  to: string;
  subject: string;
  body: string;
  approvalStatus: ApprovalStatus;
}) {
  assertApproved("send_email", _input.approvalStatus);
  if (!sendEmailTransportAvailable()) {
    throw new PolicyBlockedError("Email transport is not wired in Phase 2.");
  }
  throw new PolicyBlockedError("Unreachable");
}
