# Quickstart: Validating Desktop Entries

**Feature**: [spec.md](spec.md) | **Contracts**: [contracts/desktop-source.md](contracts/desktop-source.md)

## Prerequisites

- Work inside the `gtk-dev` Distrobox container (Constitution: Development Environment).
- Build and run the development profile:

```sh
meson setup _build -Dprofile=development   # first time only
ninja -C _build
meson devenv -C _build cartridges
```

- Preferences > Import > "Desktop Entries" is on.
- For the Flatpak check (Scenario 5), build and install the Devel Flatpak from `flatpak/page.samuelm333.Cartridges.Devel.json`.

Create the test entries in `~/.local/share/applications/`. Each has `Type=Application`, `Exec=true` and `Categories=Game;`, plus:

| File | `Name=` | `Icon=` |
|------|---------|---------|
| `cart-test-missing-name.desktop` | Missing Name | `cartridges-test-does-not-exist` |
| `cart-test-missing-file.desktop` | Missing File | `/nonexistent/icon.png` |
| `cart-test-bad-file.desktop` | Bad File | `/tmp/cart-test-bad.png` (create with `echo x > /tmp/cart-test-bad.png`) |
| `cart-test-no-icon.desktop` | No Icon | (omit the key) |
| `cart-test-theme.desktop` | Theme Icon | an icon installed in hicolor, such as `steam` or `org.gnome.Chess` |
| `cart-test-ext.desktop` | Ext Icon | the same name with `.png` appended |
| `cart-test-pixmap.desktop` | Pixmap Icon | a name that exists only in `/usr/share/pixmaps` on the host, such as `cupsprinter` |
| `cart-test-path.desktop` | Path Icon | absolute path to an existing PNG or SVG, such as `/usr/share/icons/hicolor/48x48/apps/<something>.png` |

Remove them afterwards with `rm ~/.local/share/applications/cart-test-*.desktop /tmp/cart-test-bad.png`.

## Automated checks

```sh
pre-commit run --all-files
pyright
ninja -C _build test
python tests/test_desktop.py
python tests/test_importer.py
python tests/test_saved_library.py
```

Expected: all pass. `test_desktop.py` covers contract C-1 (filtering and every icon outcome). `test_importer.py` covers C-3 and C-4.

## Scenario 1: No broken icons (US1, FR-014, FR-015, SC-001)

1. Start Cartridges with the test entries present (or press Preferences > Import > Import Now).
2. Open the Desktop source in the sidebar.
3. Expected: Missing Name, Missing File, Bad File and No Icon each show the generic application icon, centered on the cover. None shows a broken-image icon.

## Scenario 2: Real icons still show (US1, FR-012, FR-013, SC-002)

1. Same library as Scenario 1.
2. Expected: Theme Icon, Ext Icon, Pixmap Icon and Path Icon each show their own icon, not the generic one. Optionally compare with upstream `main` (`~/Development/cartridges-main`): the same entries resolve to the same icons there.

## Scenario 3: Saved covers are repaired (US2, FR-016, FR-017, SC-003)

1. On `main` (before the fix), import the test entries, so Missing Name is saved with a broken icon. Quit.
2. Switch to the fix branch, rebuild, and turn "Import Games on Startup" off. Start Cartridges.
3. Expected: Missing Name still shows the broken icon (the saved cover is loaded, no scan has run yet).
4. Press Import Now.
5. Expected: Missing Name now shows the generic application icon. Quit and start again with the switch still off.
6. Expected: the generic icon is still shown (it was saved).
7. Repeat steps 1 to 3 with "Import Games on Startup" on. Expected: the generic icon is shown right after the start, and after a second restart with the switch off.

## Scenario 4: Custom covers are kept (US2, FR-016, SC-004)

1. Open Theme Icon's details, choose a local image as its cover, and apply.
2. Press Import Now. Expected: the custom cover remains.
3. Restart with "Import Games on Startup" on. Expected: the custom cover remains.
4. Delete the custom cover in details and press Import Now. Expected: the theme icon cover returns.

## Scenario 5: Flatpak (edge case)

1. In the installed Devel Flatpak, repeat Scenarios 1 and 2. For Path Icon, use a host path under `/usr/share/...` that does not exist in the GNOME runtime.
2. Expected: the same results as natively. The host path icon is found through `/run/host`.

## Scenario 6: Filtering unchanged (US3, FR-001 to FR-011, SC-005)

1. Compare the list of Desktop games before and after the fix on the same system. Expected: identical titles.
2. Add `NoDisplay=true` to one test entry and press Import Now. Expected: it disappears.
3. Play Theme Icon. Expected: the entry launches (`Exec=true` exits immediately; check with a visible command such as `Exec=gnome-calculator` if needed).
