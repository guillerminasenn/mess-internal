#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_PY="$SCRIPT_DIR/run.py"
LOG_DIR="$SCRIPT_DIR/logs"
PYTHON_BIN="/home/senng/mess-internal/.venv-mess/bin/python"

GRID_COUNT=${1:-12}

mkdir -p "$LOG_DIR"

if [[ "$GRID_COUNT" -lt 1 ]]; then
  echo "GRID_COUNT must be >= 1" >&2
  exit 1
fi

if [[ "$GRID_COUNT" -gt 12 ]]; then
  echo "GRID_COUNT capped at 12 by request; using 12."
  GRID_COUNT=12
fi

echo "Launching $GRID_COUNT workers..."
for i in $(seq 0 $((GRID_COUNT - 1))); do
  LOG_FILE="$LOG_DIR/worker_${i}.log"
  echo "  worker $i -> $LOG_FILE"
  "$PYTHON_BIN" "$RUN_PY" --grid-count "$GRID_COUNT" --grid-index "$i" > "$LOG_FILE" 2>&1 &
done

echo "Done."
echo "Track status with: tail -f $LOG_DIR/worker_0.log"
echo "Active job PIDs:"
jobs -p || true
