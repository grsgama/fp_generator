#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/grsgama/Repositorio/fp_generator"
PID_FILE="$APP_DIR/fp_generator.pid"
UNIT_NAME="fp_generator"

is_app_pid() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && ps -p "$pid" -o args= 2>/dev/null | grep -F "uvicorn" | grep -F "app:app" >/dev/null
}

if command -v systemctl >/dev/null 2>&1 && systemctl --user --quiet is-active "$UNIT_NAME.service"; then
  systemctl --user stop "$UNIT_NAME.service"
  echo "App finalizado ($UNIT_NAME.service)."
  rm -f "$PID_FILE"
  exit 0
fi

if [[ ! -f "$PID_FILE" ]]; then
  echo "Nenhum PID file encontrado."
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "${PID:-}" ]]; then
  echo "PID invalido."
  rm -f "$PID_FILE"
  exit 0
fi

if is_app_pid "$PID"; then
  kill "$PID"
  sleep 1
  if is_app_pid "$PID"; then
    kill -9 "$PID" || true
  fi
  echo "App finalizado (PID $PID)."
else
  echo "PID $PID nao corresponde ao app."
fi

rm -f "$PID_FILE"
