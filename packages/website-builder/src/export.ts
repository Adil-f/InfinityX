import fs from "fs";
import path from "path";
import { createHash } from "crypto";
import { spawnSync } from "child_process";

export function exportDirectoryToZip(sourceDir: string, zipPath: string): string {
  fs.mkdirSync(path.dirname(zipPath), { recursive: true });
  if (fs.existsSync(zipPath)) fs.unlinkSync(zipPath);
  const absZip = path.resolve(zipPath);
  const res = spawnSync("zip", ["-r", absZip, "."], { cwd: sourceDir, encoding: "utf8" });
  if (res.status !== 0) {
    throw new Error(`zip failed: ${res.stderr || res.stdout}`);
  }
  const buf = fs.readFileSync(absZip);
  return createHash("sha256").update(buf).digest("hex");
}

export function checksumDir(dir: string): string {
  const hash = createHash("sha256");
  const walk = (d: string) => {
    for (const name of fs.readdirSync(d).sort()) {
      const p = path.join(d, name);
      const st = fs.statSync(p);
      if (st.isDirectory()) walk(p);
      else {
        hash.update(name);
        hash.update(fs.readFileSync(p));
      }
    }
  };
  walk(dir);
  return hash.digest("hex");
}
