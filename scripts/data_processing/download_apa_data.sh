#!/usr/bin/env bash
# =============================================================================
# download_apa_data.sh — Prioritized FASTQ Batch Downloader for ApaData
# =============================================================================
# Downloads long-read RNA-seq FASTQ files from SRA/ENA based on metadata
# in total_rna_samples_final.tsv.
#
# Input : total_rna_samples_final.tsv
#         Columns: species, sra_id, platform, sample_source, source_name,
#                  sample_condition
#
# Output: /home/zjzace/Desktop/disk1/ApaData/{species}/{sample_source}/{source_name}/
#
# Download cascade (per SRA ID): ascp → lftp → prefetch + fasterq-dump
# Tier priority: Tier1 (normal/WT/unknown) → Tier2 (partial match) → Tier3
# Platform sub-sort: PacBio first, then Nanopore, within each tier
#
# Usage:
#   bash download_apa_data.sh
#   nohup bash download_apa_data.sh > download_apa_data.log 2>&1 &
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#readonly INPUT_TSV="${SCRIPT_DIR}/processed_cell_line_filtered_final.tsv"
readonly INPUT_TSV="${SCRIPT_DIR}/tissue_samples_normal.tsv"

readonly BASEDIR="/home/zjzace/Desktop/disk1/BioProject/ApaData"
readonly ATLAS_DIR="/home/zjzace/ApaAtlas"
readonly MAIN_LOG="${BASEDIR}/download_apa_data_tissue.log"
readonly FAILED_LOG="${BASEDIR}/failed_downloads_tissue.tsv"

# Size limits
readonly SOFT_CAP_BYTES=128849018880      # 120 GB
readonly MIN_FILES_BEFORE_CAP=3
readonly FREE_SPACE_CRITICAL_BYTES=107374182400  # 100 GB

# Tool timeouts (seconds)
readonly TIMEOUT_ASCP=720000
readonly TIMEOUT_LFTP=720000
readonly TIMEOUT_PREFETCH=720000

# Retry policy
readonly MAX_ATTEMPTS=1

# SRA toolkit path (full path since not always in PATH)
readonly PREFETCH_BIN="/home/zjzace/software/sratoolkit.3.3.0-alma_linux64/bin/prefetch"
readonly FASTERQ_BIN="/home/zjzace/software/sratoolkit.3.3.0-alma_linux64/bin/fasterq-dump"

# Alert email
readonly ALERT_EMAIL="zjzace@outlook.com"
readonly DISK_MOUNT="/home/zjzace/Desktop/disk1"

# Lock file for thread-safe logging (single-threaded in this script, kept for safety)
readonly LOCK_FILE="${BASEDIR}/.download_apa.lock"

# =============================================================================
# FIND ASPERA BINARY AND KEY
# =============================================================================

_find_ascp_bin() {
    local candidates=(
        "$HOME/.aspera/connect/bin/ascp"
        "$HOME/.aspera/cli/bin/ascp"
    )
    for b in "${candidates[@]}"; do
        [[ -x "${b}" ]] && echo "${b}" && return
    done
    command -v ascp 2>/dev/null || true
}

_find_ascp_key() {
    local candidates=(
        "$HOME/.aspera/connect/etc/asperaweb_id_dsa.openssh"
        "$HOME/.aspera/cli/etc/asperaweb_id_dsa.openssh"
    )
    for k in "${candidates[@]}"; do
        [[ -s "${k}" ]] && echo "${k}" && return
    done
}

ASCP_BIN=$(_find_ascp_bin)
ASCP_KEY=$(_find_ascp_key)
readonly ASCP_BIN ASCP_KEY

# =============================================================================
# LOGGING
# =============================================================================

log() {
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${ts}] $*" | tee -a "${MAIN_LOG}"
}

log_failed() {
    local sra_id="$1" species="$2" sample_source="$3" source_name="$4" reason="$5"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    (
        flock -w 5 200
        echo -e "${sra_id}\t${species}\t${sample_source}\t${source_name}\t${reason}\t${ts}" \
            >> "${FAILED_LOG}"
    ) 200>"${LOCK_FILE}"
}

# =============================================================================
# INITIALIZATION
# =============================================================================

init() {
    mkdir -p "${BASEDIR}"

    if [[ ! -f "${MAIN_LOG}" ]]; then
        touch "${MAIN_LOG}"
    fi

    if [[ ! -f "${FAILED_LOG}" ]]; then
        echo -e "SRA_ID\tSpecies\tSampleSource\tSourceName\tReason\tTimestamp" \
            > "${FAILED_LOG}"
    fi

    if [[ ! -f "${INPUT_TSV}" ]]; then
        log "ERROR: Input TSV not found: ${INPUT_TSV}"
        exit 1
    fi
}

# =============================================================================
# DISK SPACE GUARD (Step 8)
# =============================================================================
# Check available free space on the target disk.
# If below critical threshold, send alert email and sleep in background,
# re-checking every 20 minutes until space recovers above 100 GB.

readonly DISK_WAIT_INTERVAL=1200   # 20 minutes in seconds

check_disk_space() {
    local free_bytes
    free_bytes=$(df -B1 "${DISK_MOUNT}" 2>/dev/null | awk 'NR==2{print $4}')

    if (( free_bytes < FREE_SPACE_CRITICAL_BYTES )); then
        local free_gb=$(( free_bytes / 1073741824 ))
        log "CRITICAL: Only ${free_gb} GB free on ${DISK_MOUNT}. Threshold is 100 GB."
        #send_alert_email "${free_gb}"
        log "Pausing downloads — will recheck disk space every 20 minutes."

        while true; do
            sleep "${DISK_WAIT_INTERVAL}"
            free_bytes=$(df -B1 "${DISK_MOUNT}" 2>/dev/null | awk 'NR==2{print $4}')
            free_gb=$(( free_bytes / 1073741824 ))
            log "Disk space check: ${free_gb} GB free on ${DISK_MOUNT}."
            if (( free_bytes >= FREE_SPACE_CRITICAL_BYTES )); then
                log "Disk space recovered (${free_gb} GB free). Resuming downloads."
                break
            fi
            log "Still low (${free_gb} GB free). Continuing to wait..."
        done
    fi
}

# =============================================================================
# EMAIL ALERT (Step 8)
# =============================================================================

# send_alert_email() {
#     local free_gb="${1:-unknown}"
#     local ts
#     ts=$(date '+%Y-%m-%d %H:%M:%S')
#     local body
#     body="$(cat <<EOF
# Disk Space Critical Alert
# =========================
# Time      : ${ts}
# Mount     : ${DISK_MOUNT}
# Free Space: ${free_gb} GB  (threshold: 100 GB)

# The download script download_apa_data.sh has been paused to prevent
# the filesystem from filling up. It will automatically resume once free
# space exceeds 100 GB (rechecking every 20 minutes).

# Script: ${SCRIPT_DIR}/download_apa_data.sh
# Log   : ${MAIN_LOG}
# EOF
# )"
#     echo "${body}" | mail -s "Disk Space Critical" "${ALERT_EMAIL}" 2>/dev/null \
#         || log "WARNING: Failed to send alert email (mail command failed)"
# }

# =============================================================================
# FOLDER SIZE / FILE COUNT HELPERS (Step 6)
# =============================================================================

get_folder_size() {
    local dir="$1"
    if [[ -d "${dir}" ]]; then
        du -sb "${dir}" 2>/dev/null | awk '{print $1}' || echo 0
    else
        echo 0
    fi
}

count_fastq_files() {
    local dir="$1"
    if [[ -d "${dir}" ]]; then
        find "${dir}" -maxdepth 1 -name "*.fastq.gz" -size +0c 2>/dev/null | wc -l
    else
        echo 0
    fi
}

# =============================================================================
# ENA PATH HELPERS
# =============================================================================
# EBI FTP/fasp directory path for a given SRA accession.
# The structure is /vol1/fastq/PREFIX/[SUFFIX]/ACCESSION/
#   PREFIX  = first 6 chars  (e.g., ERR290 from ERR2902198)
#   SUFFIX  = depends on total accession length:
#     9 chars  → no sub-dir   (e.g., SRR000001  → /vol1/fastq/SRR000/SRR000001)
#    10 chars  → 00X          (e.g., SRR1234567 → /vol1/fastq/SRR123/007/SRR1234567)
#    11 chars  → 0XX          (e.g., SRR12345678→ /vol1/fastq/SRR123/078/SRR12345678)
#    12 chars  → XXX          (e.g., SRR123456789→/vol1/fastq/SRR123/789/SRR123456789)

ena_path() {
    local run_id="$1"
    local prefix="${run_id:0:6}"
    local len="${#run_id}"
    local suffix
    case "${len}" in
        9)  suffix="" ;;
        10) suffix="00${run_id: -1}" ;;
        11) suffix="0${run_id: -2}" ;;
        12) suffix="${run_id: -3}" ;;
        *)  suffix="" ;;
    esac

    if [[ -n "${suffix}" ]]; then
        echo "/vol1/fastq/${prefix}/${suffix}/${run_id}"
    else
        echo "/vol1/fastq/${prefix}/${run_id}"
    fi
}

# =============================================================================
# ENA API: FETCH FASTQ FILENAMES FOR A RUN
# =============================================================================
# Returns newline-separated basenames of available FASTQ files for a run.
# Falls back to guessing default names if the API fails or returns nothing.

get_ena_fastq_filenames() {
    local run_id="$1"
    local api_url
    api_url="https://www.ebi.ac.uk/ena/portal/api/filereport?accession=${run_id}&result=read_run&fields=fastq_ftp"
    local response
    response=$(curl -s --max-time 30 "${api_url}" 2>/dev/null || true)

    local ftp_field
    ftp_field=$(echo "${response}" | awk -F'\t' 'NR==2{print $2}')

    if [[ -z "${ftp_field}" ]]; then
        # Fallback: guess default filename
        echo "${run_id}.fastq.gz"
        return
    fi

    # ftp_field is semicolon-separated full FTP paths — extract basenames
    local IFS=';'
    for path in ${ftp_field}; do
        [[ -n "${path}" ]] && basename "${path}"
    done
}

# =============================================================================
# EXTRACT SRA ACCESSION ID FROM FILENAME (Step 1)
# =============================================================================
# Given a filename (basename), extract the leading SRA accession.
# Handles:
#   ERR2902198.fastq.gz               → ERR2902198
#   SRR6666823_subreads_pacbio.fastq.gz → SRR6666823
#   SRR14635691_1.fastq.gz            → SRR14635691

extract_sra_id_from_filename() {
    local filename
    filename=$(basename "$1")
    # Match leading [SED]RR followed by digits — stop at underscore or dot
    echo "${filename}" | grep -oP '^[SED]RR[0-9]+' || true
}

# =============================================================================
# BUILD INDEX OF ALREADY-DOWNLOADED FILES (Step 1)
# =============================================================================
# Populates the associative array DOWNLOADED_INDEX:
#   key   = SRA accession (e.g., SRR14635691)
#   value = newline-separated list of full file paths

declare -A DOWNLOADED_INDEX

build_download_index() {
    log "Building index of already-downloaded files in ${ATLAS_DIR} ..."
    local count=0

    while IFS= read -r -d '' filepath; do
        local accession
        accession=$(extract_sra_id_from_filename "${filepath}")
        if [[ -n "${accession}" ]]; then
            if [[ -n "${DOWNLOADED_INDEX[${accession}]+x}" ]]; then
                DOWNLOADED_INDEX["${accession}"]="${DOWNLOADED_INDEX[${accession}]}"$'\n'"${filepath}"
            else
                DOWNLOADED_INDEX["${accession}"]="${filepath}"
            fi
            (( count++ )) || true
        fi
    done < <(find "${ATLAS_DIR}" -name "*.gz" -print0 2>/dev/null)

    log "Index built: ${count} .gz file(s) found across ${#DOWNLOADED_INDEX[@]} unique accession(s)."
}

# =============================================================================
# GZIP HELPER
# =============================================================================

gzip_fastq_files() {
    local run_id="$1"
    local output_dir="$2"

    for f in "${output_dir}/${run_id}.fastq" \
              "${output_dir}/${run_id}_1.fastq" \
              "${output_dir}/${run_id}_2.fastq" \
              "${output_dir}/${run_id}_subreads.fastq"; do
        if [[ -f "${f}" ]]; then
            log "  Compressing ${f} ..."
            pigz -p 8 "${f}" 2>/dev/null || gzip "${f}"
        fi
    done
}

# =============================================================================
# PACBIO RENAME (Step 5 — Step 3 of download logic)
# =============================================================================
# Renames all {run_id}*.fastq.gz → {run_id}*_pacbio.fastq.gz
# Inserts _pacbio before the final .fastq.gz extension.
# Skips files already tagged.

rename_for_pacbio() {
    local run_id="$1"
    local output_dir="$2"

    while IFS= read -r src; do
        [[ -z "${src}" ]] && continue
        local bname
        bname=$(basename "${src}" .fastq.gz)
        # Avoid double-tagging
        if [[ "${bname}" == *_pacbio ]]; then
            continue
        fi
        local dst="${output_dir}/${bname}_pacbio.fastq.gz"
        mv "${src}" "${dst}"
        log "  Renamed to PacBio: $(basename "${dst}")"
    done < <(find "${output_dir}" -maxdepth 1 -name "${run_id}*.fastq.gz" -size +0c 2>/dev/null)
}

# =============================================================================
# FILE VALIDATION
# =============================================================================

validate_gz_file() {
    local f="$1"
    # Use pigz for parallel integrity check (falls back to gzip if pigz unavailable)
    if command -v pigz &>/dev/null; then
        pigz -t "${f}" 2>/dev/null && return 0 || return 1
    else
        gzip -t "${f}" 2>/dev/null && return 0 || return 1
    fi
}

validate_run_files() {
    local run_id="$1"
    local output_dir="$2"

    local files=()
    while IFS= read -r -d '' f; do
        files+=("$f")
    done < <(find "${output_dir}" -maxdepth 1 -name "${run_id}*.fastq.gz" -size +0c -print0 2>/dev/null)

    if [[ ${#files[@]} -eq 0 ]]; then
        return 1
    fi

    local all_ok=0
    for f in "${files[@]}"; do
        if ! validate_gz_file "${f}"; then
            log "  CORRUPT file detected and removed: ${f}"
            rm -f "${f}"
            all_ok=1
        fi
    done
    return "${all_ok}"
}

# =============================================================================
# CLEANUP PARTIAL FILES FOR A RUN ID
# =============================================================================
# Removes all intermediate / partial files left by a failed download attempt:
#   - {run_id}*.fastq.gz  (partial gz from ascp/lftp)
#   - {run_id}*.fastq     (uncompressed output from fasterq-dump)
#   - {run_id}*.fastq.gz.partial  (ascp resume checkpoints)
#   - {run_id}*.fastq.gz.aspx    (ascp manifest files)
# The .sra_cache sub-directory is managed by download_prefetch itself.

cleanup_partial_files() {
    local run_id="$1"
    local output_dir="$2"

    local removed=0
    while IFS= read -r -d '' f; do
        rm -f "${f}" 2>/dev/null && (( removed++ )) || true
    done < <(find "${output_dir}" -maxdepth 1 \( \
        -name "${run_id}*.fastq.gz"         \
        -o -name "${run_id}*.fastq"         \
        -o -name "${run_id}*.fastq.gz.partial" \
        -o -name "${run_id}*.fastq.gz.aspx" \
    \) -print0 2>/dev/null)

    if (( removed > 0 )); then
        log "  Cleaned ${removed} partial file(s) for ${run_id} in ${output_dir}"
    fi
}

# =============================================================================
# DOWNLOAD METHOD 1: ascp (EBI Aspera fasp)
# =============================================================================

download_ascp() {
    local run_id="$1"
    local output_dir="$2"

    if [[ -z "${ASCP_BIN}" || ! -x "${ASCP_BIN}" ]]; then
        log "  SKIP ascp for ${run_id}: ascp binary not found"
        return 1
    fi
    if [[ -z "${ASCP_KEY}" || ! -s "${ASCP_KEY}" ]]; then
        log "  SKIP ascp for ${run_id}: ascp key not found"
        return 1
    fi

    local ena_dir
    ena_dir=$(ena_path "${run_id}")

    # Fetch the list of expected filenames from ENA API
    local filenames=()
    mapfile -t filenames < <(get_ena_fastq_filenames "${run_id}")
    if [[ ${#filenames[@]} -eq 0 ]]; then
        filenames=("${run_id}.fastq.gz")
    fi

    log "  TRYING ascp for ${run_id} (${#filenames[@]} file(s)) ..."

    local all_ok=0
    for fname in "${filenames[@]}"; do
        [[ -z "${fname}" ]] && continue
        local fasp_url="era-fasp@fasp.sra.ebi.ac.uk:${ena_dir}/${fname}"
        local exit_code=0
        timeout "${TIMEOUT_ASCP}" "${ASCP_BIN}" \
            -QT -l 300m -P33001 -k1 \
            -i "${ASCP_KEY}" \
            "${fasp_url}" \
            "${output_dir}/" >> "${MAIN_LOG}" 2>&1 || exit_code=$?

        if [[ ${exit_code} -ne 0 ]]; then
            log "  ascp FAILED for ${fname} (exit code ${exit_code})"
            rm -f "${output_dir}/${fname}" \
                  "${output_dir}/${fname}.partial" \
                  "${output_dir}/${fname}.aspx" 2>/dev/null || true
            all_ok=1
            continue
        fi

        if [[ ! -s "${output_dir}/${fname}" ]]; then
            log "  ascp produced empty file for ${fname}"
            rm -f "${output_dir}/${fname}" \
                  "${output_dir}/${fname}.partial" \
                  "${output_dir}/${fname}.aspx" 2>/dev/null || true
            all_ok=1
            continue
        fi

        log "  ascp OK: ${fname}"
    done

    if [[ ${all_ok} -ne 0 ]]; then
        log "  FAILED ascp for ${run_id}: one or more files failed"
        cleanup_partial_files "${run_id}" "${output_dir}"
        return 1
    fi

    log "  SUCCESS ascp for ${run_id}"
    return 0
}

# =============================================================================
# DOWNLOAD METHOD 2: lftp (EBI FTP)
# =============================================================================

download_lftp() {
    local run_id="$1"
    local output_dir="$2"

    if ! command -v lftp &>/dev/null; then
        log "  SKIP lftp for ${run_id}: lftp not in PATH"
        return 1
    fi

    local ena_dir
    ena_dir=$(ena_path "${run_id}")

    log "  TRYING lftp for ${run_id} ..."

    local exit_code=0
    timeout "${TIMEOUT_LFTP}" lftp -e "
        set net:timeout 120;
        set net:max-retries 3;
        set net:reconnect-interval-base 10;
        set ftp:passive-mode true;
        open ftp://ftp.sra.ebi.ac.uk;
        mirror --parallel=32 --include-glob='${run_id}*.fastq.gz' \
            ${ena_dir}/ \
            ${output_dir}/;
        quit
    " >> "${MAIN_LOG}" 2>&1 || exit_code=$?

    if [[ ${exit_code} -ne 0 ]]; then
        cleanup_partial_files "${run_id}" "${output_dir}"
        log "  FAILED lftp for ${run_id} (exit code ${exit_code})"
        return 1
    fi

    if ! find "${output_dir}" -maxdepth 1 \
        -name "${run_id}*.fastq.gz" -size +0c 2>/dev/null | grep -q .; then
        cleanup_partial_files "${run_id}" "${output_dir}"
        log "  FAILED lftp for ${run_id}: no output files found"
        return 1
    fi

    log "  SUCCESS lftp for ${run_id}"
    return 0
}

# =============================================================================
# DOWNLOAD METHOD 3: prefetch + fasterq-dump (NCBI SRA Toolkit fallback)
# =============================================================================

download_prefetch() {
    local run_id="$1"
    local output_dir="$2"

    if [[ ! -x "${PREFETCH_BIN}" ]]; then
        log "  SKIP prefetch for ${run_id}: prefetch not found at ${PREFETCH_BIN}"
        return 1
    fi
    if [[ ! -x "${FASTERQ_BIN}" ]]; then
        log "  SKIP prefetch for ${run_id}: fasterq-dump not found at ${FASTERQ_BIN}"
        return 1
    fi

    log "  TRYING prefetch for ${run_id} ..."

    local sra_cache_dir="${output_dir}/.sra_cache"
    mkdir -p "${sra_cache_dir}"

    local exit_code=0

    # Try ascp transport first; fall back to HTTPS
    timeout "${TIMEOUT_PREFETCH}" "${PREFETCH_BIN}" \
        --transport fasp \
        --max-size 100G \
        -O "${sra_cache_dir}" \
        "${run_id}" >> "${MAIN_LOG}" 2>&1 || exit_code=$?

    if [[ ${exit_code} -ne 0 ]] || [[ ! -d "${sra_cache_dir}/${run_id}" ]]; then
        log "  prefetch ascp transport failed, retrying via HTTPS ..."
        exit_code=0
        timeout "${TIMEOUT_PREFETCH}" "${PREFETCH_BIN}" \
            --max-size 100G \
            -O "${sra_cache_dir}" \
            "${run_id}" >> "${MAIN_LOG}" 2>&1 || exit_code=$?
    fi

    if [[ ${exit_code} -ne 0 ]]; then
        log "  FAILED prefetch for ${run_id} (exit code ${exit_code})"
        rm -rf "${sra_cache_dir}/${run_id}" 2>/dev/null || true
        cleanup_partial_files "${run_id}" "${output_dir}"
        return 1
    fi

    # Reject fast5 / tar.gz data
    if find "${sra_cache_dir}/${run_id}" \
        \( -name "*.fast5" -o -name "*.tar.gz" \) 2>/dev/null | grep -q .; then
        log "  SKIP ${run_id}: prefetch downloaded fast5 or tar.gz data"
        rm -rf "${sra_cache_dir}/${run_id}" 2>/dev/null || true
        return 2
    fi

    # Locate the .sra file
    local sra_file
    sra_file=$(find "${sra_cache_dir}/${run_id}" -name "*.sra" 2>/dev/null | head -1)
    if [[ -z "${sra_file}" || ! -f "${sra_file}" ]]; then
        log "  FAILED prefetch for ${run_id}: .sra file not found after prefetch"
        rm -rf "${sra_cache_dir}/${run_id}" 2>/dev/null || true
        return 1
    fi

    log "  Running fasterq-dump for ${run_id} ..."
    exit_code=0
    "${FASTERQ_BIN}" \
        --threads 4 \
        --split-3 \
        -O "${output_dir}" \
        "${sra_file}" >> "${MAIN_LOG}" 2>&1 || exit_code=$?

    if [[ ${exit_code} -ne 0 ]]; then
        log "  FAILED fasterq-dump for ${run_id} (exit code ${exit_code})"
        rm -rf "${sra_cache_dir}/${run_id}" 2>/dev/null || true
        cleanup_partial_files "${run_id}" "${output_dir}"
        return 1
    fi

    # Compress uncompressed output
    gzip_fastq_files "${run_id}" "${output_dir}"

    # Clean up SRA cache
    rm -rf "${sra_cache_dir}/${run_id}" 2>/dev/null || true

    log "  SUCCESS prefetch for ${run_id}"
    return 0
}

# =============================================================================
# CORE: DOWNLOAD ONE SRA ID (Step 5)
# =============================================================================
# Tries download methods in order: ascp → lftp → prefetch+fasterq-dump.
# Retries once on failure. Applies PacBio rename if needed.
#
# Arguments:
#   $1 run_id       — SRA accession
#   $2 output_dir   — Destination folder
#   $3 platform     — Platform string from TSV
#   $4 species      — For logging
#   $5 sample_source — For logging
#   $6 source_name  — For logging
#
# Returns:
#   0 — success (file(s) present and valid)
#   1 — all methods failed
#   2 — permanently skipped (e.g. fast5/tar format)

download_sra() {
    local run_id="$1"
    local output_dir="$2"
    local platform="$3"
    local species="$4"
    local sample_source="$5"
    local source_name="$6"

    log "  Downloading ${run_id} (cascade: ascp → lftp → prefetch, one attempt each) ..."

    local dl_rc=1

    # --- Method 1: ascp ---
    download_ascp "${run_id}" "${output_dir}" && dl_rc=0 || dl_rc=$?
    if [[ ${dl_rc} -eq 0 ]]; then
        log "  Validating ${run_id} after ascp ..."
        if ! validate_run_files "${run_id}" "${output_dir}"; then
            log "  Validation FAILED after ascp for ${run_id} — falling through to lftp"
            cleanup_partial_files "${run_id}" "${output_dir}"
            dl_rc=1
        fi
    fi

    # --- Method 2: lftp ---
    if [[ ${dl_rc} -ne 0 ]]; then
        cleanup_partial_files "${run_id}" "${output_dir}"
        download_lftp "${run_id}" "${output_dir}" && dl_rc=0 || dl_rc=$?
        if [[ ${dl_rc} -eq 0 ]]; then
            log "  Validating ${run_id} after lftp ..."
            if ! validate_run_files "${run_id}" "${output_dir}"; then
                log "  Validation FAILED after lftp for ${run_id} — falling through to prefetch"
                cleanup_partial_files "${run_id}" "${output_dir}"
                dl_rc=1
            fi
        fi
    fi

    # --- Method 3: prefetch + fasterq-dump ---
    if [[ ${dl_rc} -ne 0 ]]; then
        cleanup_partial_files "${run_id}" "${output_dir}"
        download_prefetch "${run_id}" "${output_dir}" && dl_rc=0 || dl_rc=$?
        if [[ ${dl_rc} -eq 2 ]]; then
            log_failed "${run_id}" "${species}" "${sample_source}" "${source_name}" \
                "fast5_or_tar_format"
            return 2
        fi
        if [[ ${dl_rc} -eq 0 ]]; then
            log "  Validating ${run_id} after prefetch ..."
            if ! validate_run_files "${run_id}" "${output_dir}"; then
                log "  Validation FAILED after prefetch for ${run_id} — all methods exhausted"
                cleanup_partial_files "${run_id}" "${output_dir}"
                dl_rc=1
            fi
        fi
    fi

    if [[ ${dl_rc} -ne 0 ]]; then
        log "  FAILED ${run_id}: all methods exhausted"
        log_failed "${run_id}" "${species}" "${sample_source}" "${source_name}" \
            "all_methods_failed"
        return 1
    fi

    # Apply PacBio rename if needed
    local lower_platform
    lower_platform=$(echo "${platform}" | tr '[:upper:]' '[:lower:]')
    if echo "${lower_platform}" | grep -qiE "pacbio|PACBIO_SMRT"; then
        rename_for_pacbio "${run_id}" "${output_dir}"
    fi

    log "  SUCCESS ${run_id}"
    return 0
}

# =============================================================================
# PLATFORM CLASSIFICATION HELPERS (Step 4)
# =============================================================================

is_pacbio() {
    local platform="$1"
    echo "${platform}" | grep -qiE "pacbio|PACBIO_SMRT" && return 0 || return 1
}

is_nanopore() {
    local platform="$1"
    echo "${platform}" | grep -qiE "nanopore|OXFORD_NANOPORE|ONT" && return 0 || return 1
}

# =============================================================================
# TIER CLASSIFICATION (Step 4)
# =============================================================================
# Returns:
#   1 — exact match: unknown / wild type / normal
#   2 — contains "wild type" or "normal"
#   3 — everything else

classify_tier() {
    local condition="$1"
    local lower
    lower=$(echo "${condition}" | tr '[:upper:]' '[:lower:]' | xargs)  # xargs trims whitespace

    # Tier 1: exact match
    if [[ "${lower}" == "wt" || "${lower}" == "wild type" || "${lower}" == "normal" || "${lower}" == "unknown" ]]; then
        echo 1
        return
    fi

    # Tier 2: contains "control", but do not contain '+' (to avoid complex conditions)
    if echo "${lower}" | grep -qiE "control" && ! echo "${lower}" | grep -q '+'; then
        echo 2
        return
    fi

    # Tier 3: everything else
    echo 3
}

# =============================================================================
# SHUFFLE HELPER
# =============================================================================
# Reads lines from stdin, shuffles them, writes to stdout.

shuffle_lines() {
    shuf
}

# =============================================================================
# PARALLEL DOWNLOAD SLOT MANAGER
# =============================================================================
readonly PARALLEL_DOWNLOADS=2

# Script-level state for the job manager — reset by process_folder each call.
declare -A _RUNNING_JOBS   # pid → result_file path
_ANY_FAILED=false          # set to true when a job exits with rc != 0 and != 2
_CAP_HIT=false             # set to true when folder size cap is reached
_JOB_TMP_DIR=""            # mktemp dir for per-job result files

_launch_download_job() {
    local result_file="$1"
    local sra_id="$2"
    local dest_dir="$3"
    local platform="$4"
    local species="$5"
    local sample_source="$6"
    local source_name="$7"

    (
        local dl_result=0
        download_sra "${sra_id}" "${dest_dir}" "${platform}" \
            "${species}" "${sample_source}" "${source_name}" || dl_result=$?
        echo "${sra_id}:${dl_result}" > "${result_file}"
    ) &
}

_wait_one_job() {
    local finished_pid
    finished_pid=$(
        for pid in "${!_RUNNING_JOBS[@]}"; do
            if ! kill -0 "${pid}" 2>/dev/null; then
                echo "${pid}"
                break
            fi
        done
    )

    if [[ -z "${finished_pid}" ]]; then
        wait -n 2>/dev/null || true
        for pid in "${!_RUNNING_JOBS[@]}"; do
            if ! kill -0 "${pid}" 2>/dev/null; then
                finished_pid="${pid}"
                break
            fi
        done
    fi

    [[ -z "${finished_pid}" ]] && return

    local res_file="${_RUNNING_JOBS[${finished_pid}]}"
    unset "_RUNNING_JOBS[${finished_pid}]"
    wait "${finished_pid}" 2>/dev/null || true

    if [[ -f "${res_file}" ]]; then
        local result_line job_sra job_rc
        result_line=$(cat "${res_file}" 2>/dev/null || true)
        job_sra="${result_line%%:*}"
        job_rc="${result_line##*:}"
        rm -f "${res_file}" 2>/dev/null || true

        case "${job_rc}" in
            0)  log "  DONE ${job_sra}" ;;
            2)  log "  SKIP (permanently) ${job_sra}" ;;
            *)  log "  FAILED ${job_sra} — all methods exhausted"
                _ANY_FAILED=true ;;
        esac
    fi
}

_drain_jobs() {
    while [[ ${#_RUNNING_JOBS[@]} -gt 0 ]]; do
        _wait_one_job
    done
}

# =============================================================================
# PROCESS ONE DESTINATION FOLDER (Steps 3–7)
# =============================================================================
# Arguments:
#   $1 dest_dir        — Full path to destination folder
#   $2 species         — Original species string (for logging/failed log)
#   $3 sample_source   — Original sample_source
#   $4 source_name     — Original source_name
#   $5+ sra_entries    — Space-separated "sra_id|platform|sample_condition" triples

process_folder() {
    local dest_dir="$1"
    local species="$2"
    local sample_source="$3"
    local source_name="$4"
    shift 4
    # remaining args: "sra_id|platform|sample_condition" entries
    local entries=("$@")

    log "-------------------------------------------------------------------"
    log "FOLDER: ${dest_dir}"
    log "  Group: ${species} / ${sample_source} / ${source_name}"
    log "  Total SRA IDs in group: ${#entries[@]}"

    # ------------------------------------------------------------------
    # Step 3: Skip if folder is already complete
    # ------------------------------------------------------------------
    mkdir -p "${dest_dir}"

    if [[ -f "${dest_dir}/download.completed" ]]; then
        log "  SKIP: download.completed marker present"
        return
    fi

    local apa_sites_count summary_count
    apa_sites_count=$(find "${dest_dir}" -maxdepth 1 -name "*apa_sites.txt" ! -empty 2>/dev/null | wc -l)
    summary_count=$(find "${dest_dir}" -maxdepth 1 -name "*summary.txt" ! -empty 2>/dev/null | wc -l)

    if (( apa_sites_count > 0 && summary_count > 0 )); then
        log "  SKIP: folder already contains *apa_sites.txt and *summary.txt"
        return
    fi

    # ------------------------------------------------------------------
    # Step 4: Sort entries into tiers with platform sub-sort
    # ------------------------------------------------------------------
    # Build per-(tier, platform) buckets as temporary arrays
    local t1_pacbio=()
    local t1_nanopore=()
    local t2_pacbio=()
    local t2_nanopore=()
    local t3_pacbio=()
    local t3_nanopore=()

    for entry in "${entries[@]}"; do
        local sra_id platform condition
        IFS='|' read -r sra_id platform condition <<< "${entry}"

        local tier
        tier=$(classify_tier "${condition}")

        if is_pacbio "${platform}"; then
            case "${tier}" in
                1) t1_pacbio+=("${sra_id}|${platform}|${condition}") ;;
                2) t2_pacbio+=("${sra_id}|${platform}|${condition}") ;;
                3) t3_pacbio+=("${sra_id}|${platform}|${condition}") ;;
            esac
        elif is_nanopore "${platform}"; then
            case "${tier}" in
                1) t1_nanopore+=("${sra_id}|${platform}|${condition}") ;;
                2) t2_nanopore+=("${sra_id}|${platform}|${condition}") ;;
                3) t3_nanopore+=("${sra_id}|${platform}|${condition}") ;;
            esac
        else
            # Non-PacBio, non-Nanopore — treat as Nanopore bucket for ordering
            case "${tier}" in
                1) t1_nanopore+=("${sra_id}|${platform}|${condition}") ;;
                2) t2_nanopore+=("${sra_id}|${platform}|${condition}") ;;
                3) t3_nanopore+=("${sra_id}|${platform}|${condition}") ;;
            esac
        fi
    done

    # Shuffle within each (tier, platform) bucket
    local sorted_entries=()

    # Helper: shuffle array into sorted_entries
    _append_shuffled() {
        local arr=("$@")
        if [[ ${#arr[@]} -gt 0 ]]; then
            local shuffled
            mapfile -t shuffled < <(printf '%s\n' "${arr[@]}" | shuffle_lines)
            sorted_entries+=("${shuffled[@]}")
        fi
    }

    _append_shuffled "${t1_pacbio[@]+"${t1_pacbio[@]}"}"
    _append_shuffled "${t1_nanopore[@]+"${t1_nanopore[@]}"}"
    _append_shuffled "${t2_pacbio[@]+"${t2_pacbio[@]}"}"
    _append_shuffled "${t2_nanopore[@]+"${t2_nanopore[@]}"}"
    _append_shuffled "${t3_pacbio[@]+"${t3_pacbio[@]}"}"
    _append_shuffled "${t3_nanopore[@]+"${t3_nanopore[@]}"}"

    log "  Processing order (${#sorted_entries[@]} entries):"
    log "    Tier1-PacBio: ${#t1_pacbio[@]}  Tier1-Nanopore: ${#t1_nanopore[@]}"
    log "    Tier2-PacBio: ${#t2_pacbio[@]}  Tier2-Nanopore: ${#t2_nanopore[@]}"
    log "    Tier3-PacBio: ${#t3_pacbio[@]}  Tier3-Nanopore: ${#t3_nanopore[@]}"

    # ------------------------------------------------------------------
    # Step 5: Download / Move logic — 2 parallel jobs per folder
    # ------------------------------------------------------------------
    _JOB_TMP_DIR=$(mktemp -d "${BASEDIR}/.job_tmp_XXXXXX")
    trap 'rm -rf "${_JOB_TMP_DIR}" 2>/dev/null || true' RETURN
    _RUNNING_JOBS=()
    _ANY_FAILED=false
    _CAP_HIT=false
    local entry_idx=0
    local total_entries="${#sorted_entries[@]}"

    # ------------------------------------------------------------------
    # Main dispatch loop
    # ------------------------------------------------------------------
    for entry in "${sorted_entries[@]}"; do
        (( entry_idx++ )) || true
        local sra_id platform condition
        IFS='|' read -r sra_id platform condition <<< "${entry}"

        # Global disk space guard before each dispatch
        check_disk_space

        # Step 6: Check folder size/file count BEFORE dispatching next download.
        # Use a conservative check: also count in-flight jobs as potential data.
        local folder_size file_count
        folder_size=$(get_folder_size "${dest_dir}")
        file_count=$(count_fastq_files "${dest_dir}")

        if (( folder_size >= SOFT_CAP_BYTES && file_count >= MIN_FILES_BEFORE_CAP )); then
            log "  CAP REACHED for ${dest_dir}: ${folder_size} bytes, ${file_count} files"
            _CAP_HIT=true

            # Drain currently running jobs before marking remaining as skipped
            _drain_jobs

            # Log ALL remaining unprocessed entries (current + rest) as cap-skipped
            # Current entry (entry_idx already incremented above) is the first skip
            local skip_entries=("${entry}")
            for (( si = entry_idx; si < total_entries; si++ )); do
                skip_entries+=("${sorted_entries[${si}]}")
            done

            for skip_entry in "${skip_entries[@]}"; do
                local sk_id sk_platform sk_condition
                IFS='|' read -r sk_id sk_platform sk_condition <<< "${skip_entry}"
                log "  CAP SKIP: ${sk_id} (folder size limit reached)"
                log_failed "${sk_id}" "${species}" "${sample_source}" "${source_name}" \
                    "folder_size_cap_skip"
            done
            break
        fi

        log "  Processing SRA ID: ${sra_id}  [platform: ${platform}, condition: ${condition}]"

        # ---- Step 5.1: Check if already downloaded (from ATLAS index) ----
        if [[ -n "${DOWNLOADED_INDEX[${sra_id}]+x}" ]]; then
            log "  FOUND in index: ${sra_id} — moving to ${dest_dir}/"
            local moved_any=false
            while IFS= read -r src_file; do
                [[ -z "${src_file}" ]] && continue
                if [[ -f "${src_file}" ]]; then
                    local bname
                    bname=$(basename "${src_file}")
                    local dst_file="${dest_dir}/${bname}"
                    mv "${src_file}" "${dst_file}" \
                        && log "  MOVED: ${src_file} → ${dst_file}" \
                        || log "  WARNING: Failed to move ${src_file}"
                    moved_any=true
                else
                    log "  WARNING: Indexed file no longer exists: ${src_file}"
                fi
            done <<< "${DOWNLOADED_INDEX[${sra_id}]}"

            # Apply PacBio tag if needed after move
            local lower_platform
            lower_platform=$(echo "${platform}" | tr '[:upper:]' '[:lower:]')
            if echo "${lower_platform}" | grep -qiE "pacbio"; then
                rename_for_pacbio "${sra_id}" "${dest_dir}"
            fi

            if [[ "${moved_any}" == "true" ]]; then
                continue
            fi
            # If file was missing despite index, fall through to download
            log "  All indexed files missing — falling through to download"
        fi

        # ---- Step 5.2: Check if already downloaded in dest_dir itself ----
        if find "${dest_dir}" -maxdepth 1 -name "${sra_id}*.fastq.gz" -size +0c \
            2>/dev/null | grep -q .; then
            log "  SKIP ${sra_id}: already present in ${dest_dir}"
            continue
        fi

        # ---- Step 5.3: Dispatch download (parallel slot management) ----
        log "  Queuing download: ${sra_id} to ${dest_dir} ..."

        # If at capacity, wait for one slot to free up before launching
        while (( ${#_RUNNING_JOBS[@]} >= PARALLEL_DOWNLOADS )); do
            _wait_one_job
        done

        local res_file="${_JOB_TMP_DIR}/${sra_id}.result"
        _launch_download_job "${res_file}" "${sra_id}" "${dest_dir}" "${platform}" \
            "${species}" "${sample_source}" "${source_name}"
        _RUNNING_JOBS[$!]="${res_file}"
        log "  Launched job PID=$! for ${sra_id} (${#_RUNNING_JOBS[@]}/${PARALLEL_DOWNLOADS} slots used)"
    done

    # Drain any remaining in-flight jobs
    _drain_jobs

    # ------------------------------------------------------------------
    # Step 7: Decide whether to mark folder complete
    # ------------------------------------------------------------------
    local final_size final_files final_gb
    final_size=$(get_folder_size "${dest_dir}")
    final_files=$(count_fastq_files "${dest_dir}")
    final_gb=$(awk "BEGIN{printf \"%.2f\", ${final_size}/1073741824}")

    log "  Finished folder: ${dest_dir}"
    log "  Final state: ${final_files} FASTQ file(s), ${final_gb} GB"

    if [[ "${_CAP_HIT}" == "true" ]]; then
        touch "${dest_dir}/download.completed"
        log "  MARKED COMPLETE (folder size cap): ${dest_dir}/download.completed"
    elif [[ "${_ANY_FAILED}" == "false" ]]; then
        touch "${dest_dir}/download.completed"
        log "  MARKED COMPLETE (all IDs succeeded): ${dest_dir}/download.completed"
    else
        log "  NOT marked complete: one or more IDs failed to download (folder size < 50 GB)"
    fi
}

# =============================================================================
# PARSE TSV AND BUILD FOLDER GROUPS (Step 2)
# =============================================================================
# Reads the TSV (skipping header), normalizes folder paths,
# and builds a mapping from folder key → list of "sra_id|platform|condition".

read_tsv_and_dispatch() {
    # Associative arrays: key = "species_dir|sample_source_dir|source_name_dir"
    declare -A group_entries     # key → tab-separated "sra|platform|condition" entries (newline-delimited)
    declare -A group_species     # key → original species
    declare -A group_source      # key → original sample_source
    declare -A group_name        # key → original source_name
    declare -A group_dest        # key → full destination folder path
    declare -a group_keys_ordered  # ordered unique keys (insertion order)

    local line_num=0

    while IFS=$'\t' read -r col_species col_sra_id col_platform col_sample_source col_source_name col_condition; do
        (( line_num++ )) || true

        # Strip Windows \r from all fields (TSV may have CRLF line endings)
        col_species="${col_species//$'\r'/}"
        col_sra_id="${col_sra_id//$'\r'/}"
        col_platform="${col_platform//$'\r'/}"
        col_sample_source="${col_sample_source//$'\r'/}"
        col_source_name="${col_source_name//$'\r'/}"
        col_condition="${col_condition//$'\r'/}"

        # Skip header row
        if (( line_num == 1 )) && [[ "${col_species}" == "species" ]]; then
            continue
        fi

        # Skip blank or malformed rows
        if [[ -z "${col_species}" || -z "${col_sra_id}" ]]; then
            continue
        fi

        # ---- Step 2: Build destination folder path ----
        # Replace ALL spaces with underscores in the three path components
        local sp_dir src_dir name_dir
        sp_dir=$(echo "${col_species}"      | tr ' ' '_')
        src_dir=$(echo "${col_sample_source}" | tr ' ' '_')
        name_dir=$(echo "${col_source_name}"  | tr ' ' '_')

        local dest_path="${BASEDIR}/${sp_dir}/${src_dir}/${name_dir}"
        local key="${sp_dir}|${src_dir}|${name_dir}"

        if [[ -z "${group_entries[${key}]+x}" ]]; then
            group_entries["${key}"]=""
            group_species["${key}"]="${col_species}"
            group_source["${key}"]="${col_sample_source}"
            group_name["${key}"]="${col_source_name}"
            group_dest["${key}"]="${dest_path}"
            group_keys_ordered+=("${key}")
        fi

        # Append entry as "sra_id|platform|condition"
        local entry="${col_sra_id}|${col_platform}|${col_condition}"
        if [[ -z "${group_entries[${key}]}" ]]; then
            group_entries["${key}"]="${entry}"
        else
            group_entries["${key}"]="${group_entries[${key}]}"$'\n'"${entry}"
        fi

    done < "${INPUT_TSV}"

    log "Parsed ${#group_keys_ordered[@]} unique (species / sample_source / source_name) folder group(s)."

    # ---- Process each folder group ----
    for key in "${group_keys_ordered[@]}"; do
        local dest="${group_dest[${key}]}"
        local sp="${group_species[${key}]}"
        local src="${group_source[${key}]}"
        local nm="${group_name[${key}]}"

        # Convert newline-delimited entries to array
        local entries_arr=()
        while IFS= read -r entry_line; do
            [[ -n "${entry_line}" ]] && entries_arr+=("${entry_line}")
        done <<< "${group_entries[${key}]}"

        process_folder "${dest}" "${sp}" "${src}" "${nm}" "${entries_arr[@]}"
    done
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    # Ensure base directories exist and log files are initialized
    init

    log "=================================================================="
    log "  ApaData Downloader starting"
    log "  Input TSV : ${INPUT_TSV}"
    log "  Output dir: ${BASEDIR}"
    log "  Atlas dir : ${ATLAS_DIR} (source for pre-downloaded files)"
    log "  Download cascade: ascp → lftp → prefetch+fasterq-dump"
    log "  Folder cap: ${SOFT_CAP_BYTES} bytes (120 GB) with min ${MIN_FILES_BEFORE_CAP} files"
    log "  Disk guard: ${FREE_SPACE_CRITICAL_BYTES} bytes (100 GB) free required"
    log "=================================================================="

    # Initial disk space check
    check_disk_space

    # Step 1: Build index of already-downloaded files from ApaAtlas
    build_download_index

    # Steps 2–7: Parse TSV, group by folder, sort by tier/platform, download/move
    read_tsv_and_dispatch

    # Clean up lock file
    rm -f "${LOCK_FILE}" 2>/dev/null || true

    log "=================================================================="
    log "  All folder groups processed."
    log "=================================================================="
}

# =============================================================================
# ENTRY POINT
# =============================================================================

main "$@"
