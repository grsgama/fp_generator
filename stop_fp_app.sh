#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/grsgama/Repositorio/fp_generator"
PID_FILE="$APP_DIR/streamlit.pid"

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

if ps -p "$PID" >/dev/null 2>&1; then
  kill "$PID"
  sleep 1
  if ps -p "$PID" >/dev/null 2>&1; then
    kill -9 "$PID" || true
  fi
  echo "App finalizado (PID $PID)."
else
  echo "Processo PID $PID já não estava ativo."
fi

rm -f "$PID_FILE"
