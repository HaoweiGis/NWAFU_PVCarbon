#!/usr/bin/env bash
set -euo pipefail

ROOT=${CCD_ROOT:-/data/hdd/haoweimu/datasets/D010_CCD_2001-2024}
URL='https://china.scidb.cn/getZipFile?dataSetId=9df1ab40944b4ce58eec7265462b4247&version=V1'
NAME='9df1ab40944b4ce58eec7265462b4247_V1.zip'
EXPECTED_BYTES=10163712508
ARIA2=${ARIA2_BIN:-/home/server/Python_env/haoweimu/bin/aria2c}

PARTIAL_DIR="$ROOT/downloads/partial"
RAW_DIR="$ROOT/raw"
CHECKSUM_DIR="$ROOT/checksums"
LOG_DIR="$ROOT/logs"
PARTIAL="$PARTIAL_DIR/$NAME"
FINAL="$RAW_DIR/$NAME"
LOG="$LOG_DIR/download_$(date +%Y%m%dT%H%M%S).log"

mkdir -p "$PARTIAL_DIR" "$RAW_DIR" "$CHECKSUM_DIR" "$LOG_DIR" "$ROOT/metadata"
exec > >(tee -a "$LOG") 2>&1

printf 'START\t%s\n' "$(date -Is)"
printf 'ROOT\t%s\n' "$ROOT"
printf 'URL\t%s\n' "$URL"
printf 'EXPECTED_BYTES\t%s\n' "$EXPECTED_BYTES"

if [[ -f "$FINAL" ]]; then
  actual=$(stat -c %s "$FINAL")
  [[ "$actual" -eq "$EXPECTED_BYTES" ]]
  unzip -t "$FINAL" >/dev/null
  printf 'ALREADY_VERIFIED\t%s\n' "$FINAL"
  exit 0
fi

[[ -x "$ARIA2" ]]
"$ARIA2" \
  --continue=true \
  --max-connection-per-server=2 \
  --split=2 \
  --min-split-size=64M \
  --file-allocation=none \
  --auto-file-renaming=false \
  --allow-overwrite=true \
  --retry-wait=15 \
  --max-tries=20 \
  --timeout=120 \
  --dir="$PARTIAL_DIR" \
  --out="$NAME" \
  "$URL"

actual=$(stat -c %s "$PARTIAL")
[[ "$actual" -eq "$EXPECTED_BYTES" ]]
unzip -t "$PARTIAL" >/dev/null

digest=$(sha256sum "$PARTIAL" | cut -d' ' -f1)
printf '%s  %s\n' "$digest" "$NAME" | tee "$CHECKSUM_DIR/${NAME}.sha256"
mv "$PARTIAL" "$FINAL"

printf 'PROMOTED\t%s\t%s\n' "$actual" "$FINAL"
printf 'FINISH\t%s\n' "$(date -Is)"
