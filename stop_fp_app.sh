#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/grsgama/Repositorio/fp_generator"
STREAMLIT_BIN="/home/grsgama/miniconda3/envs/fp_generator/bin/streamlit"
PID_FILE="$APP_DIR/streamlit.pid"
UNIT_NAME="fp_generator"

is_app_pid() {
  local pid="${1:-}"
  [[ -n "$pid" ]] && ps -p "$pid" -o args= 2>/dev/null | grep -F "$STREAMLIT_BIN" | grep -F "app.py" >/dev/null
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
  echo "PID inválido."
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
  echo "PID $PID não corresponde ao app."
fi

rm -f "$PID_FILE"
