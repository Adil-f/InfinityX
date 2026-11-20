import { getDb } from "@infinityx/db";
import { dbPath } from "./paths";

export function db() {
  return getDb(dbPath());
}
