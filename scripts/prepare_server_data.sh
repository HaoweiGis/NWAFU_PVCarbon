#!/usr/bin/env bash
set -euo pipefail

ROOT=${NWA_PVCARBON_ROOT:-/data/ssd/haoweimu/NWAFU_PVCarbon}
MODE=${1:-prepare}

mkdir -p \
  "$ROOT"/{00_admin/{manifests,metadata,logs,identification},01_pv,02_landcover,03_crop,04_productivity,05_carbon,06_climate,07_topography,08_infrastructure,09_boundaries,10_policy,downloads/partial,shared,scripts}

link_shared() {
  local source=$1
  local target=$2
  [[ -d "$source" ]] || { printf 'MISSING_SHARED\t%s\n' "$source" >&2; return 1; }
  if [[ -L "$target" ]]; then
    [[ "$(readlink -f "$target")" == "$(readlink -f "$source")" ]] || {
      printf 'WRONG_SYMLINK\t%s\n' "$target" >&2
      return 1
    }
  elif [[ -e "$target" ]]; then
    printf 'TARGET_EXISTS_NOT_SYMLINK\t%s\n' "$target" >&2
    return 1
  else
    ln -s "$source" "$target"
  fi
}

link_shared /data/hdd/haoweimu/datasets/D001_CLCD_2000-2025 "$ROOT/shared/CLCD_2000-2025"
link_shared /data/hdd/haoweimu/datasets/D005_ERA5_Land "$ROOT/shared/ERA5_Land"

prepare_metadata() {
  cat > "$ROOT/00_admin/manifests/BLOCKERS.tsv" <<'EOF'
id	status	detail
P0-03	PENDING_SOURCE_DECISION	Authoritative boundaries and stable administrative-code crosswalk are not frozen.
P0-04	MISSING_CRITICAL	Agricultural activity retention is required to convert PV-cropland overlap into effective cropland loss.
P0-05	PENDING_BUILD	Patch-to-Site-to-Phase aggregation and threshold validation samples are not built.
P0-06	PENDING_DESIGN	Treatment, control and placebo sample frames require a frozen identification design.
P0-07	PARTIAL_SOURCE_READY	A new stratified high-resolution validation sample is required.
P0-08	MISSING_CRITICAL	Land carbon pools, transition factors, time horizon and uncertainty are not frozen.
P0-09	MISSING_CRITICAL	The main PV dataset has no Phase-level capacity or generation.
P0-10	MISSING_CRITICAL	Marginal grid emission factors and PV lifecycle emissions are not frozen.
EOF
}

verify_pv() {
  local dataset="$ROOT/01_pv/pv_power_plants_china_2010_2022"
  local archive="$dataset/archive/PV_power_plants_China_2010_2022.zip"
  [[ -f "$archive" ]]
  (cd "$dataset" && sha256sum -c SHA256SUMS)
  unzip -t "$archive" >/dev/null
  local shp_count dbf_count shx_count prj_count
  shp_count=$(find "$dataset/raw" -type f -iname '*.shp' | wc -l)
  dbf_count=$(find "$dataset/raw" -type f -iname '*.dbf' | wc -l)
  shx_count=$(find "$dataset/raw" -type f -iname '*.shx' | wc -l)
  prj_count=$(find "$dataset/raw" -type f -iname '*.prj' | wc -l)
  [[ "$shp_count" -eq 1 && "$dbf_count" -eq 1 && "$shx_count" -eq 1 && "$prj_count" -eq 1 ]]
  printf 'PV_ARCHIVE_VERIFIED\t%s\n' "$archive"
}

show_status() {
  printf 'ROOT\t%s\n' "$ROOT"
  df -hT "$ROOT"
  printf '\n==DATASET_SIZES==\n'
  du -sh "$ROOT"/* 2>/dev/null | sort -h
  printf '\n==PARTIALS==\n'
  find "$ROOT/downloads/partial" -type f -printf '%s\t%TY-%Tm-%TdT%TH:%TM:%TS\t%p\n' | sort -k3
  printf '\n==ACTIVE_DOWNLOADS==\n'
  pgrep -af 'wget|curl.*-o|prepare_server_data.*download' || true
}

prepare_metadata
case "$MODE" in
  prepare) printf 'PREPARED\t%s\n' "$ROOT" ;;
  verify-pv) verify_pv ;;
  status) show_status ;;
  *) printf 'Usage: %s {prepare|verify-pv|status}\n' "$0" >&2; exit 2 ;;
esac
