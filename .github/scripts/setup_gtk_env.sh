#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

# Make the tests use the GNOME SDK runtime's GTK, PyGObject, and pycairo.
#
# Usage: setup_gtk_env.sh
#
# The CI image ships an older PyGObject than the runtime the app targets, and
# it does not put the runtime's shared libraries on the loader path. This
# script links only `gi` and `cairo` from the runtime (its other modules, such
# as blueprintcompiler, must not shadow the ones installed with pip) and writes
# PYTHONPATH and LD_LIBRARY_PATH to $GITHUB_ENV for the steps that follow.

set -euo pipefail

runtime=/var/lib/flatpak/runtime/org.gnome.Sdk/x86_64/50/active/files
packages="$runtime/lib/python3.13/site-packages"

if [[ -z "${GITHUB_ENV:-}" ]]; then
  echo "error: GITHUB_ENV is not set; run this script from a GitHub Actions step" >&2
  exit 1
fi

for module in gi cairo; do
  if [[ ! -d "$packages/$module" ]]; then
    echo "error: $module not found in the GNOME SDK runtime at $packages" >&2
    exit 1
  fi
done

site="$(mktemp -d)"
ln -s "$packages/gi" "$site/gi"
ln -s "$packages/cairo" "$site/cairo"

{
  echo "PYTHONPATH=$site"
  echo "LD_LIBRARY_PATH=$runtime/lib/x86_64-linux-gnu:/app/lib"
} >> "$GITHUB_ENV"
echo "Using GTK and PyGObject from $runtime"
