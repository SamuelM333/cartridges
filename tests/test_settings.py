# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test GSettings schema definitions and application color scheme synchronization."""

from pathlib import Path

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gio


def check_schema_integrity() -> None:
    """Validate that the Cartridges schema is well-formed with core keys."""
    schema_dir = Path("_build/data").resolve()
    if not schema_dir.exists():
        msg = f"Schema directory not found at {schema_dir}"
        raise FileNotFoundError(msg)

    source = Gio.SettingsSchemaSource.new_from_directory(
        str(schema_dir), Gio.SettingsSchemaSource.get_default(), False
    )
    schema = source.lookup("page.samuelm333.Cartridges", True) or source.lookup(
        "page.samuelm333.Cartridges.Devel", True
    )
    if schema is None:
        msg = "Cartridges schema not found in compiled schema directory"
        raise RuntimeError(msg)

    # Validate essential launcher preference keys
    expected_keys = {
        "exit-after-launch": "b",
        "cover-launches-game": "b",
        "high-quality-images": "b",
        "remove-missing": "b",
    }
    for key_name, expected_type in expected_keys.items():
        if not schema.has_key(key_name):
            msg = f"Required schema key '{key_name}' missing from schema"
            raise KeyError(msg)
        key = schema.get_key(key_name)
        actual_type = key.get_value_type().dup_string()
        if actual_type != expected_type:
            msg = (
                f"Key '{key_name}' has type '{actual_type}', expected '{expected_type}'"
            )
            raise TypeError(msg)

    # Verify that color-scheme is not present (no manual preference override)
    if schema.has_key("color-scheme"):
        msg = (
            "Unwanted 'color-scheme' key found; theme must synchronize with host system"
        )
        raise ValueError(msg)


def check_color_scheme_default() -> None:
    """Validate that Libadwaita StyleManager is configured for system sync."""
    style_manager = Adw.StyleManager.get_default()
    if style_manager.props.color_scheme != Adw.ColorScheme.DEFAULT:
        msg = (
            f"Expected Adw.ColorScheme.DEFAULT ({Adw.ColorScheme.DEFAULT}), "
            f"got {style_manager.props.color_scheme}"
        )
        raise ValueError(msg)


if __name__ == "__main__":
    check_schema_integrity()
    check_color_scheme_default()
