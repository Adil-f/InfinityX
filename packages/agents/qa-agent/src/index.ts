import { spawnSync } from "child_process";
import path from "path";

export function runQaAgent(payload: Record<string, unknown>) {
  const scope = String(payload.scope || "policy");
  if (scope === "policy") {
    const res = spawnSync("npm", ["run", "test", "-w", "@infinityx/policy"], {
      cwd: path.resolve(__dirname, "../../../../"),
      encoding: "utf8",
    });
    return { scope, status: res.status, out: (res.stdout || "") + (res.stderr || "") };
  }
  return { scope, status: 0, out: "skipped" };
}
