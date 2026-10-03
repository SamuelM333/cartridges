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

- **Fixed Mask Length**: When masked and an API key is configured, the field displays a fixed set amount of masked characters (e.g., 20 bullet dots) that fits the input field without disclosing the real key length or overflowing the entry width.
- **Focus Loss on Click Away**: Clicking outside the entry row or anywhere within the preferences view immediately releases focus from the entry row and commits any changes.
- **Toggle Visibility**: Clicking the eye icon toggle switches between the fixed set amount of masked characters and the actual plaintext API key.
- **Editing Flow**: When the entry row is focused for editing, the real key is loaded so the user can edit or replace it. Upon focus loss, any updated key is saved to GSettings and replaced with the fixed mask display if currently masked.
- **Keyboard & Accessibility**: Supports standard GNOME entry row interactions, including keyboard navigation, Enter/Escape to blur, and clipboard operations.
