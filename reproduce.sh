#!/usr/bin/env sh
# Linux/macOS wrapper for run_all.R. Usage: sh reproduce.sh [workers] (default 16)
set -e
here=$(cd "$(dirname "$0")" && pwd)
Rscript "$here/run_all.R" --workers "${1:-16}"
