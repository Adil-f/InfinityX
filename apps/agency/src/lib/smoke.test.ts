import { describe, expect, it } from "vitest";
import { expectedSecret } from "./auth";

describe("agency smoke", () => {
  it("has owner secret configured for local use", () => {
    expect(expectedSecret().length).toBeGreaterThan(8);
  });
});
