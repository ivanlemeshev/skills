#!/usr/bin/env bash
set -euo pipefail

if (($# < 2)); then
  printf 'Usage: bash %s HEADER COMMAND [ARGUMENT...]\n' "${0##*/}" >&2
  exit 2
fi

header=$1
shift

output_file=$(mktemp)
trap 'rm -f -- "$output_file"' EXIT

if "$@" >"$output_file" 2>&1; then
  printf '%s: OK\n' "$header"
else
  status=$?
  printf '%s: ERROR\n' "$header" >&2
  cat -- "$output_file" >&2
  exit "$status"
fi
