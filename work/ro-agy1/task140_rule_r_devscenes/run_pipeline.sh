#!/bin/bash
set -u

BASE_DIR="/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/task140_rule_r_devscenes"
CLIPS_DIR="$BASE_DIR/clips"
LOG_FILE="$BASE_DIR/pipeline.log"
PYTHON="/home/rohith/swarm-work/ro-1/py312/bin/python3"

echo "[$(date -u)] Pipeline started. Waiting for all 36 clips..." >> "$LOG_FILE"

TOTAL=36
while true; do
  python3 /home/rohith/workspaces/sclaw/agentic_colab/scripts/cosmos_queue.py fetch --owner ro-agy1 --out "$CLIPS_DIR" >> "$LOG_FILE" 2>&1
  COUNT=$(ls "$CLIPS_DIR"/t140_*.mp4 2>/dev/null | wc -l)
  echo "[$(date -u)] Fetched clips: $COUNT / $TOTAL" >> "$LOG_FILE"
  
  if [ "$COUNT" -ge "$TOTAL" ]; then
    echo "[$(date -u)] All $COUNT clips fetched!" >> "$LOG_FILE"
    break
  fi
  
  ACTIVE=$(python3 /home/rohith/workspaces/sclaw/agentic_colab/scripts/cosmos_queue.py status --owner ro-agy1 | grep "t140" | grep -E "running|pending" | wc -l)
  if [ "$ACTIVE" -eq 0 ] && [ "$COUNT" -gt 0 ]; then
    echo "[$(date -u)] No active jobs left in queue ($COUNT fetched). Proceeding with analysis." >> "$LOG_FILE"
    break
  fi
  
  sleep 20
done

echo "[$(date -u)] Running analyze_clips.py..." >> "$LOG_FILE"
$PYTHON "$BASE_DIR/analyze_clips.py" >> "$LOG_FILE" 2>&1

echo "[$(date -u)] Running nv_scoreboard scoring..." >> "$LOG_FILE"
$PYTHON /home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/nv_scoreboard/score.py "$CLIPS_DIR"/t140_*.mp4 --out "$BASE_DIR/nv_scores.json" >> "$LOG_FILE" 2>&1

echo "[$(date -u)] Running summarize_results.py..." >> "$LOG_FILE"
$PYTHON "$BASE_DIR/summarize_results.py" >> "$LOG_FILE" 2>&1

echo "[$(date -u)] Pipeline completed successfully." >> "$LOG_FILE"
