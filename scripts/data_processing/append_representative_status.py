#!/usr/bin/env python3
"""Append reference-representative transcript status to APA site tables.

The script is intentionally local-only: it reads transcript tags from the
annotation file in each species reference directory and appends one column to
the corresponding ``*_unified_apa_sites.txt`` file. Unmatched transcripts and
transcripts without a representative tag are marked ``not_representative``.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Iterable


STATUS_PRIORITY = {
    "MANE_Select": 0,
    "RefSeq_Select": 1,
    "Ensembl_Canonical": 2,
    "APPRIS_Principal": 3,
    "not_representative": 99,
}

ATTR_RE = re.compile(r'\s*([^";=\s]+)\s+(?:"([^"]*)"|([^;]*))')
GFF_ATTR_RE = re.compile(r"([^=;\s]+)=([^;]*)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append representative_status to species *_unified_apa_sites.txt files."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="IsoAPA data directory containing per-species folders.",
    )
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=Path("~/Desktop/disk1/ApaData").expanduser(),
        help="Root containing {species}/reference annotation folders.",
    )
    parser.add_argument(
        "--species",
        nargs="*",
        help="Optional species folder names to process. Defaults to all species in --data-dir.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing *.representative.txt outputs.",
    )
    return parser.parse_args()


def species_dirs(data_dir: Path, selected: list[str] | None) -> list[Path]:
    if selected:
        return sorted(data_dir / species for species in selected)
    return sorted(path for path in data_dir.iterdir() if path.is_dir())


def find_annotation_file(reference_dir: Path) -> Path | None:
    candidates: list[Path] = []
    for pattern in ("*.gtf", "*.gff3", "*.gff"):
        candidates.extend(reference_dir.glob(pattern))

    junction_files = {path for path in candidates if ".junctions." in path.name}
    candidates = [path for path in candidates if path not in junction_files]
    if not candidates:
        return None

    def rank(path: Path) -> tuple[int, str]:
        suffix_rank = 0 if path.suffix == ".gtf" else 1
        return suffix_rank, path.name

    return sorted(candidates, key=rank)[0]


def split_attr_values(value: str) -> Iterable[str]:
    for part in re.split(r"[,|]", value):
        clean = part.strip().strip('"')
        if clean:
            yield clean


def parse_attributes(attr_text: str) -> dict[str, list[str]]:
    attrs: dict[str, list[str]] = {}
    if "=" in attr_text:
        for key, value in GFF_ATTR_RE.findall(attr_text):
            attrs.setdefault(key, []).extend(split_attr_values(value))
    else:
        for chunk in attr_text.rstrip(";").split(";"):
            match = ATTR_RE.match(chunk)
            if not match:
                continue
            key = match.group(1)
            value = match.group(2) if match.group(2) is not None else match.group(3)
            attrs.setdefault(key, []).extend(split_attr_values(value or ""))
    return attrs


def get_attr(attrs: dict[str, list[str]], *keys: str) -> str | None:
    for key in keys:
        values = attrs.get(key)
        if values:
            return values[0]
    return None


def status_from_attrs(attrs: dict[str, list[str]]) -> str:
    tag_values = []
    for key in ("tag", "Tags"):
        tag_values.extend(attrs.get(key, []))
    tag_text = " ".join(tag_values)
    attr_text = " ".join(value for values in attrs.values() for value in values)

    if "MANE Select" in tag_text or "MANE_Select" in tag_text:
        return "MANE_Select"
    if "RefSeq Select" in tag_text or "RefSeq_Select" in tag_text:
        return "RefSeq_Select"
    if "Ensembl_canonical" in tag_text or "Ensembl Canonical" in tag_text:
        return "Ensembl_Canonical"
    if re.search(r"\bappris_principal(?:_\d+)?\b", attr_text, flags=re.IGNORECASE):
        return "APPRIS_Principal"
    if re.search(r"\bAPPRIS:principal(?:_\d+)?\b", attr_text):
        return "APPRIS_Principal"
    return "not_representative"


def best_status(current: str | None, candidate: str) -> str:
    if current is None:
        return candidate
    return min((current, candidate), key=lambda status: STATUS_PRIORITY.get(status, 99))


def load_representative_status(annotation_file: Path | None) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if annotation_file is None:
        return statuses

    with annotation_file.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 9:
                continue

            feature = fields[2].lower()
            if feature not in {"transcript", "mrna", "ncrna", "rrna", "trna"}:
                continue

            attrs = parse_attributes(fields[8])
            transcript_id = get_attr(attrs, "transcript_id", "ID", "transcriptId")
            if not transcript_id:
                continue
            if transcript_id.startswith("transcript:"):
                transcript_id = transcript_id.split(":", 1)[1]

            status = status_from_attrs(attrs)
            statuses[transcript_id] = best_status(statuses.get(transcript_id), status)

    return statuses


def append_status(input_file: Path, output_file: Path, statuses: dict[str, str]) -> tuple[int, int]:
    total_rows = 0
    representative_rows = 0

    with input_file.open("r", newline="", encoding="utf-8") as src, output_file.open(
        "w", newline="", encoding="utf-8"
    ) as dst:
        reader = csv.DictReader(src, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{input_file} has no header")
        if "transcript_id" not in reader.fieldnames:
            raise ValueError(f"{input_file} does not contain transcript_id")

        fieldnames = [name for name in reader.fieldnames if name != "representative_status"]
        writer = csv.DictWriter(
            dst,
            delimiter="\t",
            fieldnames=[*fieldnames, "representative_status"],
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()

        for row in reader:
            total_rows += 1
            transcript_id = row.get("transcript_id", "")
            status = statuses.get(transcript_id, "not_representative")
            if status != "not_representative":
                representative_rows += 1
            row["representative_status"] = status
            writer.writerow(row)

    return total_rows, representative_rows


def process_species(species_dir: Path, reference_root: Path, overwrite: bool) -> None:
    species = species_dir.name
    input_file = species_dir / f"{species}_unified_apa_sites.txt"
    output_file = species_dir / f"{species}_unified_apa_sites.representative.txt"

    if not input_file.exists():
        print(f"[skip] {species}: missing {input_file.name}")
        return
    if output_file.exists() and not overwrite:
        print(f"[skip] {species}: {output_file.name} exists; use --overwrite")
        return

    annotation_file = find_annotation_file(reference_root / species / "reference")
    statuses = load_representative_status(annotation_file)
    total_rows, representative_rows = append_status(input_file, output_file, statuses)
    annotation_name = annotation_file.name if annotation_file else "none"
    unique_representatives = sum(1 for status in statuses.values() if status != "not_representative")
    print(
        f"[done] {species}: rows={total_rows:,}, representative_rows={representative_rows:,}, "
        f"representative_transcripts={unique_representatives:,}, annotation={annotation_name}"
    )


def main() -> None:
    args = parse_args()
    for species_dir in species_dirs(args.data_dir, args.species):
        process_species(species_dir, args.reference_root, args.overwrite)


if __name__ == "__main__":
    main()
