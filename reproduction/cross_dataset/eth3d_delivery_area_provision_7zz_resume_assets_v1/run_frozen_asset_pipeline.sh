#!/usr/bin/env bash
set -euo pipefail

TASK_ROOT=/disk1/zlab/maintenance_records/eth3d_delivery_area_provision_7zz_resume_assets_v1
cd "$TASK_ROOT"

printf 'PHASE_START frozen_download %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 download_frozen_eth3d_assets.py
printf 'PHASE_PASS frozen_download %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

printf 'PHASE_START archive_crc_security %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 validate_7z_archives.py
printf 'PHASE_PASS archive_crc_security %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

printf 'PHASE_START quarantine_extraction %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 extract_eth3d_archives_safely.py
printf 'PHASE_PASS quarantine_extraction %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

printf 'PIPELINE_PASS %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
