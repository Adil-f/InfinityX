import { describe, expect, it } from "vitest";
import { assertApproved, canSendEmail, sendEmailTransportAvailable } from "./gates";
import { PolicyBlockedError } from "../../core/src/index";

describe("approval gates", () => {
  it("blocks unapproved send", () => {
    expect(() => assertApproved("send_email", "pending")).toThrow(PolicyBlockedError);
    expect(canSendEmail("pending")).toBe(false);
  });
  it("allows approved flag but transport stays off", () => {
    expect(() => assertApproved("send_email", "approved")).not.toThrow();
    expect(sendEmailTransportAvailable()).toBe(false);
  });
});
