#!/usr/bin/env bash
set -euo pipefail

ROOT=${PVCROP_ROOT:-/data/ssd/haoweimu/NWAFU_PVCarbon/PVCropCarbon}
set -a
source "$ROOT/config/paths.server.env"
set +a

python3 "$ROOT/scripts/preflight.py"
printf 'PRODUCTION_NOT_STARTED\tAll critical source and definition gates must pass first.\n' >&2
exit 4
