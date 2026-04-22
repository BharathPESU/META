#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  TRIAGE — Start Backend + Frontend
#  Usage:  ./start.sh
#          ./start.sh --no-mock        (use real LLM, not mocked)
#          ./start.sh --skip-install   (skip npm/pip install)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/triage-backend"
FRONTEND_DIR="$SCRIPT_DIR/triage-frontend/triage-command-center-main"

# ── Flags ─────────────────────────────────────────────────────────────────────
MOCK_LLM=true
SKIP_INSTALL=false

for arg in "$@"; do
  case $arg in
    --no-mock)        MOCK_LLM=false      ;;
    --skip-install)   SKIP_INSTALL=true   ;;
  esac
done

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m';  GREEN='\033[0;32m';  CYAN='\033[0;36m'
YELLOW='\033[1;33m';  BOLD='\033[1m';  RESET='\033[0m'

log()  { echo -e "${BOLD}[TRIAGE]${RESET} $*"; }
ok()   { echo -e "${GREEN}[OK]${RESET}     $*"; }
info() { echo -e "${CYAN}[INFO]${RESET}   $*"; }
warn() { echo -e "${YELLOW}[WARN]${RESET}   $*"; }
err()  { echo -e "${RED}[ERROR]${RESET}  $*"; }

# ── Cleanup on exit ───────────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

# Prefix strings for sed (escape codes must be literal \033 inside $'...')
BE_PFX=$'\033[0;36m[BACKEND]\033[0m '
FE_PFX=$'\033[0;32m[FRONTEND]\033[0m '

cleanup() {
  echo ""
  log "Shutting down…"
  [[ -n "$BACKEND_PID"  ]] && kill "$BACKEND_PID"  2>/dev/null && ok "Backend stopped"
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null && ok "Frontend stopped"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ── Preflight checks ──────────────────────────────────────────────────────────
log "TRIAGE — Multi-Agent Hospital Simulation"
echo "────────────────────────────────────────────────────────────"

if [[ ! -d "$BACKEND_DIR" ]]; then
  err "Backend not found at: $BACKEND_DIR"; exit 1
fi
if [[ ! -d "$FRONTEND_DIR" ]]; then
  err "Frontend not found at: $FRONTEND_DIR"; exit 1
fi

command -v python3 &>/dev/null || { err "python3 not found"; exit 1; }
command -v node    &>/dev/null || { err "node not found";    exit 1; }
command -v npm     &>/dev/null || { err "npm not found";     exit 1; }

# ── Install dependencies (optional) ──────────────────────────────────────────
if [[ "$SKIP_INSTALL" == false ]]; then
  info "Installing Python dependencies…"
  # Try venv-based install first (safe on Debian/Ubuntu 23.04+)
  VENV_DIR="$BACKEND_DIR/.venv"
  if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR" -q && ok "Created virtualenv at .venv"
  fi
  (cd "$BACKEND_DIR" && "$VENV_DIR/bin/pip" install -e ".[dev]" -q) \
    && ok "Python deps ready" \
    || warn "pip install had warnings (continuing)"

  info "Installing Node dependencies…"
  (cd "$FRONTEND_DIR" && npm install --silent) \
    && ok "Node deps ready" \
    || { err "npm install failed"; exit 1; }
else
  info "--skip-install: skipping dep installation"
  # Auto-detect venv if it exists
  VENV_DIR="$BACKEND_DIR/.venv"
fi

echo "────────────────────────────────────────────────────────────"

# ── Start Backend ─────────────────────────────────────────────────────────────
info "Starting FastAPI backend on :8000  (MOCK_LLM=$MOCK_LLM)"

# Use venv python if available, else system python3
PYTHON_BIN="python3"
[[ -f "$VENV_DIR/bin/python" ]] && PYTHON_BIN="$VENV_DIR/bin/python"

(
  cd "$BACKEND_DIR"
  export MOCK_LLM="$MOCK_LLM"
  while true; do
    "$PYTHON_BIN" -m triage.api.main 2>&1 \
      | sed "s/^/$BE_PFX/"
    warn "Backend exited — restarting in 3 s…"
    sleep 3
  done
) &
BACKEND_PID=$!

# Wait briefly for the backend to bind its port
sleep 3

# ── Health-check backend ──────────────────────────────────────────────────────
BACKEND_UP=false
for i in 1 2 3 4 5; do
  if curl -sf http://localhost:8000/api/health &>/dev/null; then
    BACKEND_UP=true; break
  fi
  sleep 2
done

if [[ "$BACKEND_UP" == true ]]; then
  ok "Backend is healthy ✓"
else
  warn "Backend health-check failed — frontend will run in MOCK mode"
fi

echo "────────────────────────────────────────────────────────────"

# ── Start Frontend ────────────────────────────────────────────────────────────
info "Starting Vite frontend on :8080"

(
  cd "$FRONTEND_DIR"
  npm run dev 2>&1 \
    | sed "s/^/$FE_PFX/"
) &
FRONTEND_PID=$!

echo "────────────────────────────────────────────────────────────"
echo -e "${BOLD}Both services are starting…${RESET}"
echo ""
echo -e "  Backend  →  ${CYAN}http://localhost:8000${RESET}"
echo -e "  Frontend →  ${GREEN}http://localhost:8080${RESET}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${RESET} to stop everything."
echo "────────────────────────────────────────────────────────────"
echo ""

# ── Wait (block until Ctrl+C) ─────────────────────────────────────────────────
wait
