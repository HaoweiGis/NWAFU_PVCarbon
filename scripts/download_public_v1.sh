#!/usr/bin/env bash
set -euo pipefail

ROOT=${NWA_PVCARBON_ROOT:-/data/ssd/haoweimu/NWAFU_PVCarbon}
MODE=${1:-prepare}
LOG="$ROOT/00_admin/logs/public_v1_$(date +%Y%m%dT%H%M%S).log"

mkdir -p \
  "$ROOT/00_admin/manifests/public_v1" \
  "$ROOT/00_admin/metadata/public_v1" \
  "$ROOT/09_boundaries/pilot_geoboundaries_adm2_2017" \
  "$ROOT/09_boundaries/pilot_gadm41" \
  "$ROOT/08_infrastructure/worldpop_1km_2000_2020" \
  "$ROOT/01_pv/capacity_calibration/wri_gppd_v1_3" \
  "$ROOT/05_carbon/soilgrids_250m_mean_0_30cm/tiles" \
  "$ROOT/05_carbon/ipcc_2019_refinement_vol4" \
  "$ROOT/downloads/partial/public_v1"

download_atomic() {
  local url=$1
  local output=$2
  local part="$ROOT/downloads/partial/public_v1/$(printf '%s' "$output" | sha256sum | cut -c1-20).part"
  mkdir -p "$(dirname "$output")"
  if [[ -s "$output" ]]; then
    printf 'EXISTS\t%s\n' "$output"
    return 0
  fi
  wget -c --retry-connrefused --waitretry=10 --timeout=120 --tries=8 -O "$part" "$url"
  [[ -s "$part" ]]
  mv "$part" "$output"
  printf 'DOWNLOADED\t%s\t%s\n' "$(stat -c %s "$output")" "$output"
}

download_core() {
  exec > >(tee -a "$LOG") 2>&1
  printf 'CORE_START\t%s\n' "$(date -Is)"

  download_atomic \
    'https://www.geoboundaries.org/api/current/gbOpen/CHN/ADM2/' \
    "$ROOT/00_admin/metadata/public_v1/geoboundaries_CHN_ADM2_api.json"
  download_atomic \
    'https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/CHN/ADM2/geoBoundaries-CHN-ADM2-all.zip' \
    "$ROOT/09_boundaries/pilot_geoboundaries_adm2_2017/geoBoundaries-CHN-ADM2-all.zip"
  unzip -t "$ROOT/09_boundaries/pilot_geoboundaries_adm2_2017/geoBoundaries-CHN-ADM2-all.zip" >/dev/null

  download_atomic \
    'https://gadm.org/license.html' \
    "$ROOT/00_admin/metadata/public_v1/gadm_license.html"
  download_atomic \
    'https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_CHN.gpkg' \
    "$ROOT/09_boundaries/pilot_gadm41/gadm41_CHN.gpkg"

  download_atomic \
    'https://raw.githubusercontent.com/wri/global-power-plant-database/master/README.md' \
    "$ROOT/00_admin/metadata/public_v1/wri_gppd_README.md"
  download_atomic \
    'https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv' \
    "$ROOT/01_pv/capacity_calibration/wri_gppd_v1_3/global_power_plant_database.csv"

  download_atomic \
    'https://www.ipcc-nggip.iges.or.jp/public/2019rf/vol4.html' \
    "$ROOT/00_admin/metadata/public_v1/ipcc_2019rf_vol4.html"
  local ipcc_base='https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4'
  for file in \
    '19R_V4_Ch02_Generic%20Methods.pdf' \
    '19R_V4_Ch03_Land%20Representation.pdf' \
    '19R_V4_Ch04_Forest%20Land.pdf' \
    '19R_V4_Ch05_Cropland.pdf' \
    '19R_V4_Ch06_Grassland.pdf' \
    '19R_V4_Ch07_Wetlands.pdf' \
    '19R_V4_Ch08_Settlements.pdf' \
    '19R_V4_Ch09_OtherLand.pdf'; do
    download_atomic "$ipcc_base/$file" "$ROOT/05_carbon/ipcc_2019_refinement_vol4/${file//%20/_}"
  done

  for year in $(seq 2000 2020); do
    download_atomic \
      "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/$year/CHN/chn_ppp_${year}_1km_Aggregated_UNadj.tif" \
      "$ROOT/08_infrastructure/worldpop_1km_2000_2020/chn_ppp_${year}_1km_Aggregated_UNadj.tif"
  done

  for dataset in \
    "$ROOT/09_boundaries/pilot_geoboundaries_adm2_2017" \
    "$ROOT/09_boundaries/pilot_gadm41" \
    "$ROOT/01_pv/capacity_calibration/wri_gppd_v1_3" \
    "$ROOT/05_carbon/ipcc_2019_refinement_vol4" \
    "$ROOT/08_infrastructure/worldpop_1km_2000_2020"; do
    (cd "$dataset" && find . -maxdepth 1 -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
  done
  printf 'CORE_FINISH\t%s\n' "$(date -Is)"
}

soilgrids_url() {
  local property=$1 depth=$2 west=$3 east=$4 south=$5 north=$6
  printf '%s' "https://maps.isric.org/mapserv?map=/map/${property}.map&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=${property}_${depth}_mean&FORMAT=image/tiff&SUBSET=long(${west},${east})&SUBSET=lat(${south},${north})&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326&OUTPUTCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
}

download_soilgrids() {
  exec > >(tee -a "$LOG") 2>&1
  printf 'SOILGRIDS_START\t%s\n' "$(date -Is)"
  download_atomic \
    'https://www.isric.org/explore/soilgrids/soilgrids-access' \
    "$ROOT/00_admin/metadata/public_v1/soilgrids_access.html"
  for property in soc bdod cfvo; do
    for depth in 0-5cm 5-15cm 15-30cm; do
      download_atomic \
        "https://files.isric.org/soilgrids/latest/data/$property/${property}_${depth}_mean.vrt" \
        "$ROOT/05_carbon/soilgrids_250m_mean_0_30cm/${property}_${depth}_mean.vrt"
      for west in 73 83 93 103 113 123 133; do
        east=$((west + 10)); [[ "$east" -le 136 ]] || east=136
        for south in 18 28 38 48; do
          north=$((south + 10)); [[ "$north" -le 54 ]] || north=54
          name="${property}_${depth}_mean_W${west}_E${east}_S${south}_N${north}.tif"
          output="$ROOT/05_carbon/soilgrids_250m_mean_0_30cm/tiles/$name"
          download_atomic "$(soilgrids_url "$property" "$depth" "$west" "$east" "$south" "$north")" "$output"
          file "$output" | grep -q 'TIFF image data'
        done
      done
    done
  done
  (cd "$ROOT/05_carbon/soilgrids_250m_mean_0_30cm" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
  printf 'SOILGRIDS_FINISH\t%s\n' "$(date -Is)"
}

show_status() {
  printf 'ROOT\t%s\n' "$ROOT"
  df -hT /data/ssd /data/hdd
  printf '\n==PUBLIC_V1_SIZES==\n'
  du -sh \
    "$ROOT/09_boundaries/pilot_geoboundaries_adm2_2017" \
    "$ROOT/09_boundaries/pilot_gadm41" \
    "$ROOT/08_infrastructure/worldpop_1km_2000_2020" \
    "$ROOT/01_pv/capacity_calibration/wri_gppd_v1_3" \
    "$ROOT/05_carbon/soilgrids_250m_mean_0_30cm" \
    "$ROOT/05_carbon/ipcc_2019_refinement_vol4" 2>/dev/null
  printf '\n==PARTIALS==\n'
  find "$ROOT/downloads/partial/public_v1" -type f -printf '%s\t%TY-%Tm-%TdT%TH:%TM:%TS\t%p\n' | sort -k3
  printf '\n==PROCESSES==\n'
  pgrep -af 'download_public_v1|maps.isric.org|data.worldpop.org|global_power_plant_database|gadm41_CHN' || true
}

case "$MODE" in
  prepare) printf 'PREPARED\t%s\n' "$ROOT" ;;
  download-core) download_core ;;
  download-soilgrids) download_soilgrids ;;
  status) show_status ;;
  *) printf 'Usage: %s {prepare|download-core|download-soilgrids|status}\n' "$0" >&2; exit 2 ;;
esac
