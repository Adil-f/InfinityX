import { PolicyBlockedError } from "../../core/src/index";
import { assertApproved, publishTransportAvailable } from "../../policy/src/gates";
import type { ApprovalStatus } from "../../core/src/index";

export async function deploy(_input: { previewId: string; approvalStatus: ApprovalStatus }) {
  assertApproved("publish_site", _input.approvalStatus);
  if (!publishTransportAvailable()) {
    throw new PolicyBlockedError("Hosting deploy is not wired in Phase 2.");
  }
}
