import { PolicyBlockedError, type ApprovalStatus } from "@infinityx/core";
import {
  assertApproved,
  publishTransportAvailable,
  sendEmailTransportAvailable,
} from "@infinityx/policy";

export async function createDraftLocal(_input: {
  to: string;
  subject: string;
  body: string;
}) {
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

export async function deploy(_input: {
  previewId: string;
  approvalStatus: ApprovalStatus;
}) {
  assertApproved("publish_site", _input.approvalStatus);
  if (!publishTransportAvailable()) {
    throw new PolicyBlockedError("Hosting deploy is not wired in Phase 2.");
  }
}

export async function purchase(_input: unknown) {
  void _input;
  throw new PolicyBlockedError(
    "Purchases are forbidden without human approval and are not implemented.",
  );
}
