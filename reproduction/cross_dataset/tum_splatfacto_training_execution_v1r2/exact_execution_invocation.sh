#!/usr/bin/env bash
set -euo pipefail

: "${PROTOCOL_DIR:?PROTOCOL_DIR must identify the frozen protocol directory}"
exec bash "$PROTOCOL_DIR/exact_training_command.sh"
