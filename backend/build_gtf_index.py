#!/usr/bin/env python3
"""
Build a byte-offset index for a GTF file, mapping transcript_id -> list of (offset, length) line spans.
This allows random access without scanning the full file.

Output: <gtf_path>.tidx  (a JSON file)
"""

import sys
import os
import json
import re
import time

TRANSCRIPT_RE = re.compile(r'transcript_id "([^"]+)"')


def build_index(gtf_path: str, index_path: str):
    print(f"Building index for {gtf_path} ...")
    t0 = time.time()

    # transcript_id -> list of (byte_offset, byte_length)
    index = {}

    with open(gtf_path, 'rb') as f:
        while True:
            offset = f.tell()
            line_bytes = f.readline()
            if not line_bytes:
                break
            if line_bytes.startswith(b'#'):
                continue
            # Only index exon/CDS/UTR/transcript feature lines
            # Quick check before decoding
            if b'transcript_id' not in line_bytes:
                continue

            line = line_bytes.decode('utf-8', errors='replace')
            fields = line.split('\t')
            if len(fields) < 9:
                continue

            feature = fields[2]
            if feature not in ('transcript', 'exon', 'CDS', 'UTR', 'three_prime_utr', 'five_prime_utr'):
                continue

            m = TRANSCRIPT_RE.search(fields[8])
            if not m:
                continue

            tid = m.group(1)
            if tid not in index:
                index[tid] = []
            index[tid].append((offset, len(line_bytes)))

    t1 = time.time()
    print(f"Indexed {len(index)} transcripts in {t1-t0:.1f}s")
    print(f"Writing index to {index_path} ...")

    with open(index_path, 'w') as f:
        json.dump(index, f)

    size_mb = os.path.getsize(index_path) / 1024 / 1024
    print(f"Done. Index size: {size_mb:.1f} MB")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python build_gtf_index.py <path/to/annotation.gtf>", file=sys.stderr)
        print("Output: <path/to/annotation.gtf>.tidx", file=sys.stderr)
        sys.exit(1)

    gtf = sys.argv[1]
    if not os.path.isfile(gtf):
        print(f"Error: GTF file not found: {gtf}", file=sys.stderr)
        sys.exit(1)

    idx = gtf + '.tidx'
    build_index(gtf, idx)
