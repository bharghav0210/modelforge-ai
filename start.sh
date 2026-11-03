#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x backend/.venv/bin/python || ! -d frontend/node_modules ]]; then
  echo 'Install dependencies first; see README.md.' >&2
  exit 1
fi
backend/.venv/bin/python - <<'PY'
import socket
for port in (3003,8003):
    with socket.socket() as sock:
        try: sock.bind(('127.0.0.1',port))
        except OSError as exc: raise SystemExit(f'Port {port} is unavailable: {exc}. No existing process was stopped.')
PY
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8003 &
backend_pid=$!
frontend_pid=''
cleanup() {
  trap - EXIT INT TERM
  kill "$backend_pid" 2>/dev/null || true
  if [[ -n "$frontend_pid" ]]; then kill "$frontend_pid" 2>/dev/null || true; fi
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM
if [[ "${1:-}" == '--production' ]]; then
  (cd frontend && exec node node_modules/next/dist/bin/next start -H 127.0.0.1 -p 3003) &
else
  (cd frontend && exec node node_modules/next/dist/bin/next dev --webpack -H 127.0.0.1 -p 3003) &
fi
frontend_pid=$!
echo 'ModelForge: http://localhost:3003 | API: http://localhost:8003/docs'
wait -n "$backend_pid" "$frontend_pid"
