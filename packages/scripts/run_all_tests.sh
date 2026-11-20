#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo "== TS tests =="
npm run test
echo "== Python tests =="
python3 -m pytest packages/scripts/tests -q
echo "== ZIP integrity =="
echo "0a0d39a10185cad29e95267ab045eadfc3c1543f4bbd01c2fd6af2d2cb0bf611  web zip.zip" | sha256sum -c -
echo "ALL OK"
