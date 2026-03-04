#!/usr/bin/env python3
"""
build_fasta_index.py  —  Build a byte-offset index for random access into a
FASTA genome file.

The index is stored as <fasta>.fidx (JSON) with the structure:
  {
    "<chrom>": {
      "offset":   <byte offset of the first nucleotide character>,
      "length":   <total number of bases>,
      "line_len": <number of bases per line (without newline)>,
      "line_bytes": <bytes per line (including newline)>
    },
    ...
  }

Usage:
    python build_fasta_index.py <genome.fa>

This script is idempotent: it skips building if the .fidx already exists and
is newer than the FASTA.
"""
import sys
import os
import json
import time


def build_index(fasta_path: str) -> None:
    idx_path = fasta_path + '.fidx'

    # Skip if index is up-to-date
    if os.path.exists(idx_path):
        if os.path.getmtime(idx_path) >= os.path.getmtime(fasta_path):
            print(f"[fasta-index] Index already up-to-date: {idx_path}", flush=True)
            return

    print(f"[fasta-index] Building index for {fasta_path} ...", flush=True)
    t0 = time.time()

    index = {}
    current_chrom = None
    first_base_offset = None
    line_len = None      # bases per line
    line_bytes = None    # bytes per line (includes \n or \r\n)
    accumulated_len = 0

    with open(fasta_path, 'rb') as fh:
        while True:
            pos = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            line = raw.decode('ascii', errors='replace')

            if line.startswith('>'):
                # Save previous entry
                if current_chrom is not None:
                    index[current_chrom] = {
                        'offset':     first_base_offset,
                        'length':     accumulated_len,
                        'line_len':   line_len,
                        'line_bytes': line_bytes,
                    }
                # New chromosome — name is everything up to first whitespace
                current_chrom = line[1:].split()[0]
                first_base_offset = None
                line_len = None
                line_bytes = None
                accumulated_len = 0
            else:
                bases = raw.rstrip(b'\r\n')
                if not bases:
                    continue
                if first_base_offset is None:
                    first_base_offset = pos
                    line_len   = len(bases)
                    line_bytes = len(raw)
                accumulated_len += len(bases)

        # Save last entry
        if current_chrom is not None:
            index[current_chrom] = {
                'offset':     first_base_offset,
                'length':     accumulated_len,
                'line_len':   line_len,
                'line_bytes': line_bytes,
            }

    with open(idx_path, 'w') as fh:
        json.dump(index, fh)

    elapsed = time.time() - t0
    chroms = len(index)
    print(f"[fasta-index] Done — {chroms} sequences indexed in {elapsed:.1f}s → {idx_path}", flush=True)


def fetch_sequence(fasta_path: str, chrom: str, start: int, end: int) -> str:
    """
    Fetch [start, end) bases (0-based, half-open) from indexed FASTA.
    Returns the raw sequence string (uppercase).
    Raises FileNotFoundError if .fidx missing, KeyError if chrom not found.
    """
    idx_path = fasta_path + '.fidx'
    with open(idx_path) as fh:
        index = json.load(fh)

    entry = index[chrom]
    offset     = entry['offset']
    line_len   = entry['line_len']
    line_bytes = entry['line_bytes']

    # Byte offset of 'start'
    lines_before_start = start // line_len
    byte_start = offset + lines_before_start * line_bytes + (start % line_len)

    # Byte offset of 'end'
    lines_before_end = (end - 1) // line_len
    byte_end = offset + lines_before_end * line_bytes + ((end - 1) % line_len) + 1

    with open(fasta_path, 'rb') as fh:
        fh.seek(byte_start)
        raw = fh.read(byte_end - byte_start)

    seq = raw.replace(b'\n', b'').replace(b'\r', b'').decode('ascii').upper()
    return seq[:end - start]   # trim to exact requested length


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <genome.fa>")
        sys.exit(1)
    build_index(sys.argv[1])
