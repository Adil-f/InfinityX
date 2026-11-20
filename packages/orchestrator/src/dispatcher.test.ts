import path from "path";
import os from "os";
import { describe, expect, it, beforeEach } from "vitest";
import { resetDbForTests, getDb } from "../../db/src/client";
import { enqueueAndRun } from "./dispatcher";

const dbPath = path.join(os.tmpdir(), `ix-orch-${Date.now()}.db`);

describe("orchestrator", () => {
  beforeEach(() => {
    resetDbForTests(dbPath);
  });

  it("runs research import job", () => {
    const db = getDb(dbPath);
    const seed = path.resolve(__dirname, "../../../data/seed/leads.seed.json");
    const { result } = enqueueAndRun(
      db,
      "research",
      { seedPath: seed },
      {
        templatesRoot: path.resolve(__dirname, "../../../templates"),
        previewsRoot: path.resolve(__dirname, "../../../data/previews"),
        exportsRoot: path.resolve(__dirname, "../../../data/exports"),
      },
    );
    expect((result as { imported: number }).imported).toBeGreaterThan(0);
  });
});
