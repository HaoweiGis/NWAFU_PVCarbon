#!/usr/bin/env python3
"""Download the three additional public-data groups required by PVCarbon V1."""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request


ROOT = Path(os.environ.get("PVCARBON_ROOT", "/data/ssd/haoweimu/NWAFU_PVCarbon"))
PARTIAL = ROOT / "downloads" / "partial" / "v1_additional"
POP_DIR = ROOT / "08_infrastructure" / "worldpop_1km_2021_2022_interim"
BIOMASS_DIR = ROOT / "05_carbon" / "esa_cci_biomass_v7_china"
PARAM_DIR = ROOT / "05_carbon" / "biomass_parameters"
GRID_DIR = ROOT / "06_electricity" / "china_grid_emission_factors_official"
NEA_DIR = ROOT / "01_pv" / "capacity_calibration" / "nea_official_2015_2022"
META_DIR = ROOT / "00_admin" / "metadata" / "v1_additional"

WGET = [
    "wget", "-c", "--retry-connrefused", "--waitretry=10", "--timeout=120",
    "--tries=8", "--no-verbose",
]


def atomic_download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 0:
        print(f"EXISTS {destination}", flush=True)
        return
    PARTIAL.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(str(destination).encode()).hexdigest()[:20]
    part = PARTIAL / f"{key}.part"
    subprocess.run(WGET + ["-O", str(part), url], check=True)
    if not part.is_file() or part.stat().st_size == 0:
        raise RuntimeError(f"empty download: {url}")
    os.replace(part, destination)
    print(f"DONE {destination} {destination.stat().st_size}", flush=True)


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "PVCarbon-data/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class PdfLinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value and value.lower().endswith(".pdf"):
                self.links.append(value)


def download_population() -> None:
    base = "https://data.worldpop.org/GIS/Population/Global_2021_2022_1km_UNadj"
    atomic_download(f"{base}/release_statement.pdf", POP_DIR / "release_statement.pdf")
    for year in (2021, 2022):
        name = f"chn_ppp_{year}_1km_UNadj.tif"
        url = f"{base}/unconstrained/{year}/CHN/{name}"
        atomic_download(url, POP_DIR / name)


def download_biomass_parameters() -> None:
    atomic_download(
        "https://www.ipcc-nggip.iges.or.jp/public/gpglulucf/"
        "gpglulucf_files/Chp3/Anx_3A_1_Data_Tables.pdf",
        PARAM_DIR / "IPCC_GPG_LULUCF_Annex_3A1_Data_Tables.pdf",
    )
    atomic_download(
        "https://artefacts.ceda.ac.uk/licences/specific_licences/"
        "esacci_biomass_terms_and_conditions_v2.pdf",
        PARAM_DIR / "ESA_CCI_Biomass_terms_and_conditions_v2.pdf",
    )
    atomic_download(
        "https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/"
        "00README_catalogue_and_licence.txt?download=1",
        PARAM_DIR / "ESA_CCI_Biomass_v7_README.txt",
    )
    ipcc_base = "https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/4_Volume4"
    for name in (
        "19R_V4_Ch02_Generic%20Methods.pdf",
        "19R_V4_Ch03_Land%20Representation.pdf",
        "19R_V4_Ch04_Forest%20Land.pdf",
        "19R_V4_Ch05_Cropland.pdf",
        "19R_V4_Ch06_Grassland.pdf",
        "19R_V4_Ch07_Wetlands.pdf",
    ):
        destination = ROOT / "05_carbon" / "ipcc_2019_refinement_vol4" / name.replace("%20", "_")
        atomic_download(f"{ipcc_base}/{name}", destination)


def download_page_pdfs(page_url: str, label: str) -> int:
    page = fetch_bytes(page_url)
    page_path = META_DIR / "grid_emission_factors" / f"{label}.html"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    page_path.write_bytes(page)
    parser = PdfLinkParser()
    parser.feed(page.decode("utf-8", errors="replace"))
    links = sorted(set(urllib.parse.urljoin(page_url, link) for link in parser.links))
    if not links:
        print(f"NO_PDF_LINKS_SAVED_HTML {page_url}", flush=True)
        return 0
    for index, url in enumerate(links, start=1):
        name = Path(urllib.parse.urlparse(url).path).name
        atomic_download(url, GRID_DIR / label / f"{index:02d}_{name}")
    return len(links)


def download_grid_factors() -> None:
    pages = {
        "MEE_2006_2016_regional_grid_baseline":
            "https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/201812/t20181220_685481.shtml",
        "MEE_2018_regional_grid_baseline":
            "https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/202012/t20201229_815384.shtml",
        "MEE_2019_regional_grid_baseline":
            "https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/202012/t20201229_815386.shtml",
        "MEE_2021_average_grid_factor":
            "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202404/t20240412_1070565.html",
        "MEE_2022_average_grid_factor":
            "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202412/t20241226_1099413.html",
    }
    for label, page_url in pages.items():
        download_page_pdfs(page_url, label)
    atomic_download(
        "https://www.mee.gov.cn/ywgz/ydqhbh/wsqtkz/201812/"
        "P020181220579925103092.pdf",
        GRID_DIR / "MEE_2017_regional_grid_baseline" / "2017_result_and_method.pdf",
    )


def download_nea_pv_statistics() -> None:
    pages = {
        2015: "https://www.nea.gov.cn/2016-02/05/c_135076636.htm",
        2016: "https://www.nea.gov.cn/2017-02/04/c_136030860.htm",
        2017: "https://www.nea.gov.cn/2018-01/24/c_136920159.htm",
        2018: "https://hzj.nea.gov.cn/dtyw/gjnyjdt/202309/t20230913_74457.html",
        2019: "https://obor.nea.gov.cn/detail/12010.html",
        2020: "https://www.nea.gov.cn/2021-01/30/c_139708580.htm",
        2021: "https://www.nea.gov.cn/2022-03/09/c_1310508114.htm",
        2022: "https://nfj.nea.gov.cn/xwzx/gjnyjdt/202308/t20230823_23732.html",
    }
    for year, url in pages.items():
        atomic_download(url, NEA_DIR / f"NEA_PV_{year}.html")


TILE_RE = re.compile(r"^(?P<ns>[NS])(?P<lat>\d{2})(?P<ew>[EW])(?P<lon>\d{3})_")


def is_china_tile(name: str) -> bool:
    match = TILE_RE.match(name)
    if not match or match.group("ns") != "N" or match.group("ew") != "E":
        return False
    lat = int(match.group("lat"))
    lon = int(match.group("lon"))
    return lat in {10, 20, 30, 40, 50} and lon in {70, 80, 90, 100, 110, 120, 130}


def download_biomass() -> None:
    years = (2010, 2011, 2012, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022)
    base = "https://data.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/geotiff"
    manifest_rows = ["year\tname\tsize\tmd5\turl"]
    selected: list[tuple[int, dict[str, object]]] = []
    for year in years:
        listing_url = f"{base}/{year}?json="
        listing_bytes = fetch_bytes(listing_url)
        listing_path = META_DIR / "esa_cci_biomass_v7" / f"{year}_listing.json"
        listing_path.parent.mkdir(parents=True, exist_ok=True)
        listing_path.write_bytes(listing_bytes)
        listing = json.loads(listing_bytes)
        for item in listing["items"]:
            name = str(item.get("name", ""))
            if not is_china_tile(name):
                continue
            if "-AGB-MERGED-" not in name and "-AGB_SD-MERGED-" not in name:
                continue
            selected.append((year, item))
            manifest_rows.append(
                f"{year}\t{name}\t{item.get('size', '')}\t{item.get('md5', '')}\t{item.get('download', '')}"
            )
    if not selected:
        raise RuntimeError("CEDA listing returned no China biomass tiles")
    expected = sum(int(item.get("size", 0)) for _, item in selected)
    free = shutil.disk_usage(ROOT).free
    if free < expected + 20 * 1024**3:
        raise RuntimeError(f"insufficient disk space: need {expected}, free {free}")
    manifest = META_DIR / "esa_cci_biomass_v7" / "selected_china_tiles.tsv"
    manifest.write_text("\n".join(manifest_rows) + "\n", encoding="utf-8")
    print(f"BIOMASS_SELECTED files={len(selected)} bytes={expected}", flush=True)
    for year, item in selected:
        destination = BIOMASS_DIR / str(year) / str(item["name"])
        atomic_download(str(item["download"]), destination)
        expected_md5 = str(item.get("md5", ""))
        if expected_md5 and md5sum(destination).lower() != expected_md5.lower():
            raise RuntimeError(f"MD5 mismatch: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "group", choices=("small", "biomass", "all"), default="all", nargs="?"
    )
    args = parser.parse_args()
    for directory in (PARTIAL, POP_DIR, BIOMASS_DIR, PARAM_DIR, GRID_DIR, NEA_DIR, META_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    if args.group in {"small", "all"}:
        download_population()
        download_biomass_parameters()
        download_grid_factors()
        download_nea_pv_statistics()
    if args.group in {"biomass", "all"}:
        download_biomass()
    return 0


if __name__ == "__main__":
    sys.exit(main())
