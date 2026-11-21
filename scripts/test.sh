#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
if [[ -x "$ROOT/backend/.venv/bin/pytest" ]]; then
  exec "$ROOT/backend/.venv/bin/pytest" -q
fi
if [[ -x /tmp/ix-venv/bin/pytest ]]; then
  exec /tmp/ix-venv/bin/pytest -q
fi
exec pytest -q
