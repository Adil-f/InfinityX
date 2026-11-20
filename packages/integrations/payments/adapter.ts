import { PolicyBlockedError } from "../../core/src/index";
export async function purchase(_input: unknown) {
  throw new PolicyBlockedError("Purchases are forbidden without human approval and are not implemented.");
}
