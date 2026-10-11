# Contract: Preferences UI and Setting

## GSettings key

```xml
<key name="debug-logs" type="b">
  <default>false</default>
</key>
```

Added to the main schema in `data/page.samuelm333.Cartridges.gschema.xml.in`. Writing the key from any place (Preferences, `gsettings set`) takes effect immediately in a running app.

## General page, new group (above "Danger Zone")

```text
Troubleshooting
+-----------------------------------------------------------+
| Debug Logs                                          [o  ] |
| Save detailed diagnostic messages to disk                 |
+-----------------------------------------------------------+
| Open Logs Folder                               [folder]   |
| ~/.var/app/page.samuelm333.Cartridges/.local/state/...    |
+-----------------------------------------------------------+
```

| Widget | Blueprint ID | Behavior |
|--------|--------------|----------|
| `Adw.PreferencesGroup` | `troubleshooting_group` | Title "Troubleshooting". Visible in every build type. |
| `Adw.SwitchRow` | `debug_logs_switch` | Bound two-way to `debug-logs` via `_bind_switches()`. |
| `Adw.ActionRow` (activatable) | `logs_folder_row` | Subtitle: log folder with home shown as `~`. Activating creates the folder if missing and opens it in the file manager. Always sensitive. |

All titles and subtitles are translatable and searchable by the dialog's search.

## Toasts

| When | Text |
|------|------|
| Folder cannot be created or a log write fails (once per run) | "Could not save debug logs" |
| Opening the folder fails | "Could not open logs folder" |
