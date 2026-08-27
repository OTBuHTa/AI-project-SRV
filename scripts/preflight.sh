#!/usr/bin/env bash
set -Eeuo pipefail

readonly PROJECT_ROOT="$(
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
  pwd
)"

cd "$PROJECT_ROOT"
exec python3 tools/srvctl --json autopilot

