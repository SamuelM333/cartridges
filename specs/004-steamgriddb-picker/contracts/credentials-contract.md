# Contract: SteamGridDB Credentials UI & GSettings

**Module**: `cartridges.ui.preferences`
**Template**: `cartridges/ui/preferences.blp`

## 1. Preferences Blueprint Definition

```blueprint
Adw.PreferencesGroup sgdb_key_group {
  title: _("Authentication");

  Adw.PasswordEntryRow sgdb_key_entry_row {
    title: _("API Key");
  }
}
```

## 2. Python Binding Contract

```python
class CartridgesPreferences(Adw.PreferencesDialog):
    sgdb_key_entry_row: Adw.PasswordEntryRow = Gtk.Template.Child()

    def _setup_steamgriddb(self) -> None:
        # Load persisted key from GSettings
        self.sgdb_key_entry_row.set_text(SETTINGS.get_string("sgdb-key"))

        def on_key_changed(row: Adw.PasswordEntryRow) -> None:
            key = row.get_text().strip()
            SETTINGS.set_string("sgdb-key", key)

        self.sgdb_key_entry_row.connect("changed", on_key_changed)
```

## 3. Behavioral Guarantees

- **Masked by default**: When opening preferences, the API key input is obscured with bullet characters.
- **Toggle visibility**: Clicking the native eye icon reveals the plaintext characters without altering the underlying string stored in `SETTINGS["sgdb-key"]`.
- **Keyboard / Accessibility**: Supports standard GNOME password row interactions, including keyboard navigation and clipboard operations.
