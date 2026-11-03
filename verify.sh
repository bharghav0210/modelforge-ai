#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
backend/.venv/bin/python -m pytest backend/tests -q
(cd frontend && npm run lint && npm run typecheck && MODELFORGE_BUILD_DIR=.next-verification npm run build)
if [[ "${1:-}" == '--browser' ]]; then
  (cd frontend && npm run test:e2e)
fi
