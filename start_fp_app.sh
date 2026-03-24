#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/grsgama/Nextcloud/LabNano/Folha de Processo/fp_generator"
STREAMLIT_BIN="/home/grsgama/miniconda3/envs/fp_generator/bin/streamlit"
PORT="${1:-8511}"
PID_FILE="$APP_DIR/streamlit.pid"
LOG_FILE="$APP_DIR/streamlit.log"

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${OLD_PID:-}" ]] && ps -p "$OLD_PID" >/dev/null 2>&1; then
    echo "App já está rodando (PID $OLD_PID, porta $PORT)."
    echo "URL: http://localhost:$PORT"
    exit 0
  fi
fi

cd "$APP_DIR"
nohup "$STREAMLIT_BIN" run app.py --server.headless true --server.port "$PORT" >"$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

sleep 1
if ps -p "$NEW_PID" >/dev/null 2>&1; then
  echo "App iniciado com sucesso."
  echo "PID: $NEW_PID"
  echo "URL: http://localhost:$PORT"
  echo "Log: $LOG_FILE"
else
  echo "Falha ao iniciar app. Verifique: $LOG_FILE"
  exit 1
fi
