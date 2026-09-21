# Quickstart Validation Guide: Publisher & FQN Update

This guide outlines the commands and steps required to build, test, and validate the updated publisher metadata and Flatpak FQN / Application ID configuration.

## 1. Prerequisites

Ensure the following tools are installed on your host system:
- Python 3
- Meson (>= 1.1.0)
- Ninja
- desktop-file-utils (for validating the desktop file)
- appstreamcli (for validating AppStream metadata)
- glib-compile-schemas (for compiling and validating GSettings schemas)

---

## 2. Build and Compilation Scenarios

Run the following commands to configure and compile the build:

```bash
# Clean up any existing build directory
rm -rf _build

# Configure the build directory for release profile
meson setup _build --prefix=/usr -Dprofile=release

# Compile all resources and schemas
meson compile -C _build
```

### Expected Outcome
The build should succeed with zero errors. Verify that the generated build outputs in `_build/data/` match the new Application ID:
- `_build/data/page.samuelm333.Cartridges.desktop`
- `_build/data/page.samuelm333.Cartridges.gschema.xml`
- `_build/data/page.samuelm333.Cartridges.metainfo.xml`
- `_build/data/page.samuelm333.Cartridges.service`

---

## 3. Validation and Automated Tests

The project uses built-in Meson test suites to validate desktop entry schemas and AppStream metadata.

Run the test suite:

```bash
meson test -C _build
```

### Expected Outcome
All validation tests must pass successfully:
1. **Validate desktop file**: Ensures the desktop file matches the standard format and points to the correct executable and icon.
2. **Validate schema file**: Compiles the schemas using `glib-compile-schemas --strict --dry-run` to ensure syntax correctness.
3. **Validate appstream file**: Runs `appstreamcli validate` to verify the `<id>`, `<developer>`, and `<url>` tags are properly structured under the new namespace without warnings or errors.

---

## 4. Manual Verification Scenarios

### Scenario A: Verify About Dialog
1. Run the application:
   ```bash
   python3 -m cartridges
   ```
2. Open the **About Cartridges** dialog.
3. Verify that:
   - **Publisher**: Displays "samuelm333" or the updated publisher website link.
   - **Authors**: The historical developer/maintainer ("kramo") remains listed in the credits, acknowledging their original contributions.

### Scenario B: Verify Game Source Blacklisting
1. Ensure `page.samuelm333.Cartridges` is installed on the system (or place a dummy desktop entry in `~/.local/share/applications`).
2. Run the application.
3. Verify that the application itself does not appear in the imported games list.

### Scenario C: Verify GNOME Builder Support
1. Launch **GNOME Builder** on your host system.
2. Select **Open Project** and navigate to your local `cartridges/` repository root.
3. Once loaded, confirm GNOME Builder has successfully parsed and selected the Flatpak configuration matching `flatpak/page.samuelm333.Cartridges.Devel.json`.
4. Click the **Run** button (or build the target project).
5. Verify the development build completes successfully and launches the application in the development profile window.


