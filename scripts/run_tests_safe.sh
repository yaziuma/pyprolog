#!/usr/bin/env bash
cd "$(dirname "$0")/.."
exec systemd-run --user --scope -p MemoryLimit=1G -p CPUQuota=20% -- uv run pytest "$@"
