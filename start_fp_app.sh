#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/grsgama/Repositorio/fp_generator"
PYTHON_BIN="$APP_DIR/.venv/bin/python"
PORT="${1:-8511}"
HOST="${2:-0.0.0.0}"
PID_FILE="$APP_DIR/fp_generator.pid"
LOG_FILE="$APP_DIR/fp_generator.log"
UNIT_NAME="fp_generator"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="/home/grsgama/miniconda3/envs/fp_generator/bin/python"
fi

is_app_pid() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && ps -p "$pid" -o args= 2>/dev/null | grep -F "uvicorn" | grep -F "app:app" >/dev/null
}

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if is_app_pid "$OLD_PID"; then
    echo "App ja esta rodando (PID $OLD_PID, porta $PORT)."
    echo "URL local: http://localhost:$PORT"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

cd "$APP_DIR"

if command -v systemd-run >/dev/null 2>&1 && systemctl --user --version >/dev/null 2>&1; then
  if systemctl --user --quiet is-active "$UNIT_NAME.service"; then
    echo "App ja esta rodando via systemd user unit ($UNIT_NAME.service, porta $PORT)."
    echo "URL local: http://localhost:$PORT"
    exit 0
  fi

  systemd-run --user --unit "$UNIT_NAME" --collect --working-directory "$APP_DIR" \
    "$PYTHON_BIN" -m uvicorn app:app --host "$HOST" --port "$PORT" >/dev/null
  sleep 1
  if systemctl --user --quiet is-active "$UNIT_NAME.service"; then
    rm -f "$PID_FILE"
    echo "App iniciado com sucesso."
    echo "Servico: $UNIT_NAME.service"
    echo "URL local: http://localhost:$PORT"
    echo "Log: journalctl --user -u $UNIT_NAME.service"
    exit 0
  fi
fi

nohup "$PYTHON_BIN" -m uvicorn app:app --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 </dev/null &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

sleep 1
if is_app_pid "$NEW_PID"; then
  echo "App iniciado com sucesso."
  echo "PID: $NEW_PID"
  echo "URL local: http://localhost:$PORT"
  echo "Log: $LOG_FILE"
else
  echo "Falha ao iniciar app. Verifique: $LOG_FILE"
  rm -f "$PID_FILE"
  exit 1
fi
