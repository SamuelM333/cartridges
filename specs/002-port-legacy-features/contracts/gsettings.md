# Contract: GSettings Schema Interface

This document specifies the contract governing persistent configuration schema keys defined under the application ID (`page.samuelm333.Cartridges`).

## 1. Schema Identifier

* **Primary Schema ID**: `page.samuelm333.Cartridges`
* **Development Schema ID**: `page.samuelm333.Cartridges.Devel`
* **Template Path**: `data/page.samuelm333.Cartridges.gschema.xml.in`

## 2. Key Groups and Binding Rules

All preferences toggles are bound bidirectionally to UI widgets using `SETTINGS.bind(key, widget, property, flags)`:

### General & Images
* `exit-after-launch` (`boolean`): Bound to `exit_after_launch_switch.active`.
* `cover-launches-game` (`boolean`): Bound to `cover_launches_game_switch.active`.
* `high-quality-images` (`boolean`): Bound to `high_quality_images_switch.active`.

### Import Behavior
* `auto-import` (`boolean`): Bound to `auto_import_switch.active`.
* `remove-missing` (`boolean`): Bound to `remove_missing_switch.active`.

### Source Toggles & Path Locations
* `{source}` (`boolean`): Enables scanning for the named source.
* `{source}-location` (`string`): Directory path where the source's data files reside.
* `{source}-import-{sub}` (`boolean`): Source-specific sub-import flags (e.g., `heroic-import-epic`).

### SteamGridDB
* `sgdb-key` (`string`): Bound to `sgdb_key_entry_row.text`.
* `sgdb` (`boolean`): Bound to `sgdb_switch.active`.
* `sgdb-prefer` (`boolean`): Bound to `sgdb_prefer_switch.active`.
* `sgdb-animated` (`boolean`): Bound to `sgdb_animated_switch.active`.
