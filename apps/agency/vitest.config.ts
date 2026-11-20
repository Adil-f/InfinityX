import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: { environment: "node" },
  resolve: {
    alias: {
      "@infinityx/core": path.resolve(__dirname, "../../packages/core/src/index.ts"),
      "@infinityx/db": path.resolve(__dirname, "../../packages/db/src/index.ts"),
      "@infinityx/policy": path.resolve(__dirname, "../../packages/policy/src/index.ts"),
      "@infinityx/orchestrator": path.resolve(__dirname, "../../packages/orchestrator/src/index.ts"),
      "@infinityx/research": path.resolve(__dirname, "../../packages/research/src/index.ts"),
      "@infinityx/website-builder": path.resolve(__dirname, "../../packages/website-builder/src/index.ts"),
    },
  },
});
