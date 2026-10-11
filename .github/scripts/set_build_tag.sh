#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

# Pass the release tag to the build so debug logs can name the version.
#
# Usage: set_build_tag.sh TAG [MANIFEST]
#
# Appends `-Dtag=TAG` to the `config-opts` of the `cartridges` module in
# MANIFEST (default: flatpak/page.samuelm333.Cartridges.json).

set -euo pipefail

tag="${1:-}"
manifest="${2:-flatpak/page.samuelm333.Cartridges.json}"

if ! command -v jq > /dev/null; then
  echo "error: jq is required but was not found in PATH" >&2
  exit 1
fi

if [[ ! "$tag" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "error: invalid tag '$tag': use letters, digits, '.', '_' and '-'" >&2
  exit 1
fi

temporary="$(mktemp)"
trap 'rm -f "$temporary"' EXIT

jq --arg tag "-Dtag=$tag" '
  (.modules[] | select(type == "object" and .name == "cartridges") | ."config-opts")
    += [$tag]
' "$manifest" > "$temporary"

jq -e --arg tag "-Dtag=$tag" '
  .modules[] | select(type == "object" and .name == "cartridges")
    | ."config-opts" | index($tag) != null
' "$temporary" > /dev/null || {
  echo "error: no 'cartridges' module found in $manifest" >&2
  exit 1
}

cat "$temporary" > "$manifest"
echo "Set build tag to $tag in $manifest"
