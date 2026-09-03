#!/usr/bin/env python3
"""Audit basic structural integrity and attributes of ESRI Shapefiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def shp_header(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 100:
        raise ValueError("file shorter than 100-byte Shapefile header")
    file_code = struct.unpack(">i", data[0:4])[0]
    declared_bytes = struct.unpack(">i", data[24:28])[0] * 2
    version, shape_type = struct.unpack("<2i", data[28:36])
    bbox = struct.unpack("<4d", data[36:68])
    return {
        "file_code": file_code,
        "declared_bytes": declared_bytes,
        "actual_bytes": len(data),
        "version": version,
        "shape_type": shape_type,
        "bbox": bbox,
    }


def shx_records(path: Path) -> tuple[dict[str, object], list[tuple[int, int]]]:
    header = shp_header(path)
    data = path.read_bytes()
    if (len(data) - 100) % 8:
        raise ValueError("SHX index section is not divisible by 8 bytes")
    records = [struct.unpack(">2i", data[i : i + 8]) for i in range(100, len(data), 8)]
    return header, records


def shp_records(path: Path) -> tuple[int, int, list[str]]:
    data = path.read_bytes()
    offset = 100
    count = 0
    null_shapes = 0
    errors: list[str] = []
    while offset < len(data):
        if offset + 8 > len(data):
            errors.append(f"truncated record header at byte {offset}")
            break
        record_no, words = struct.unpack(">2i", data[offset : offset + 8])
        content_start = offset + 8
        content_end = content_start + words * 2
        if content_end > len(data):
            errors.append(f"record {record_no} extends beyond EOF")
            break
        if words < 2:
            errors.append(f"record {record_no} has invalid content length {words}")
        else:
            shape_type = struct.unpack("<i", data[content_start : content_start + 4])[0]
            null_shapes += shape_type == 0
        count += 1
        offset = content_end
    if offset != len(data):
        errors.append(f"record scan ended at {offset}, file size is {len(data)}")
    return count, null_shapes, errors


def dbf_info(path: Path, encoding: str) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 33:
        raise ValueError("DBF file too short")
    record_count = struct.unpack("<I", data[4:8])[0]
    last_update = f"{1900 + data[1]:04d}-{data[2]:02d}-{data[3]:02d}"
    header_length, record_length = struct.unpack("<HH", data[8:12])
    fields: list[dict[str, object]] = []
    offset = 32
    while offset + 32 <= header_length and data[offset] != 0x0D:
        descriptor = data[offset : offset + 32]
        raw_name = descriptor[:11].split(b"\x00", 1)[0]
        name = raw_name.decode("ascii", errors="replace")
        fields.append(
            {
                "name": name,
                "type": chr(descriptor[11]),
                "length": descriptor[16],
                "decimal": descriptor[17],
            }
        )
        offset += 32
    minimum_bytes = header_length + record_count * record_length
    samples: list[dict[str, str]] = []
    values_by_field: dict[str, list[str]] = {str(field["name"]): [] for field in fields}
    for row_index in range(record_count):
        row_start = header_length + row_index * record_length
        row = data[row_start : row_start + record_length]
        values: dict[str, str] = {}
        cursor = 1
        for field in fields:
            width = int(field["length"])
            raw = row[cursor : cursor + width]
            name = str(field["name"])
            values[name] = raw.decode(encoding, errors="replace").strip()
            values_by_field[name].append(values[name])
            cursor += width
        if row_index < 3:
            samples.append(values)
    field_stats = {}
    for name, values in values_by_field.items():
        nonempty = [value for value in values if value]
        field_stats[name] = {
            "nonempty": len(nonempty),
            "unique_nonempty": len(set(nonempty)),
            "duplicate_nonempty": len(nonempty) - len(set(nonempty)),
            "replacement_character_values": sum("�" in value for value in nonempty),
            "lengths": sorted({len(value) for value in nonempty}),
        }
    return {
        "record_count": record_count,
        "last_update": last_update,
        "header_length": header_length,
        "record_length": record_length,
        "minimum_bytes": minimum_bytes,
        "actual_bytes": len(data),
        "fields": fields,
        "field_stats": field_stats,
        "samples": samples,
    }


def audit_layer(shp_path: Path) -> dict[str, object]:
    stem = shp_path.with_suffix("")
    required = {suffix: stem.with_suffix(suffix) for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg")}
    missing = [suffix for suffix, path in required.items() if not path.is_file()]
    if missing:
        return {"layer": shp_path.stem, "status": "FAIL", "missing": missing}
    encoding = required[".cpg"].read_text(encoding="ascii", errors="replace").strip() or "utf-8"
    shp = shp_header(required[".shp"])
    shx, index = shx_records(required[".shx"])
    record_count, null_shapes, record_errors = shp_records(required[".shp"])
    dbf = dbf_info(required[".dbf"], encoding)
    errors = list(record_errors)
    if shp["file_code"] != 9994 or shx["file_code"] != 9994:
        errors.append("invalid Shapefile code")
    if shp["version"] != 1000 or shx["version"] != 1000:
        errors.append("invalid Shapefile version")
    if shp["declared_bytes"] != shp["actual_bytes"]:
        errors.append("SHP declared size differs from actual size")
    if shx["declared_bytes"] != shx["actual_bytes"]:
        errors.append("SHX declared size differs from actual size")
    if not (record_count == len(index) == dbf["record_count"]):
        errors.append(
            f"record count mismatch: shp={record_count}, shx={len(index)}, dbf={dbf['record_count']}"
        )
    for position, length in index:
        if position * 2 < 100 or position * 2 + 8 + length * 2 > int(shp["actual_bytes"]):
            errors.append("SHX contains an out-of-range record")
            break
    return {
        "layer": shp_path.stem,
        "status": "PASS" if not errors else "FAIL",
        "encoding": encoding,
        "crs_wkt": required[".prj"].read_text(encoding="utf-8", errors="replace").strip(),
        "sha256": {
            suffix: hashlib.sha256(path.read_bytes()).hexdigest()
            for suffix, path in required.items()
        },
        "shape_type": shp["shape_type"],
        "bbox": shp["bbox"],
        "records": record_count,
        "null_shapes": null_shapes,
        "dbf_last_update": dbf["last_update"],
        "fields": dbf["fields"],
        "field_stats": dbf["field_stats"],
        "samples": dbf["samples"],
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    results = [audit_layer(path) for path in sorted(args.directory.rglob("*.shp"))]
    text = json.dumps(results, ensure_ascii=False, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")
    raise SystemExit(1 if any(item["status"] != "PASS" for item in results) else 0)


if __name__ == "__main__":
    main()
