# Data Model: Publisher & Application ID Migration

This document defines the configuration, settings, and metadata structures (the "data models") affected by the transition to the updated Flatpak FQN and Application ID.

## 1. Core Identifiers Model

| Variable | Old Value | New Value | Environment / Profile |
|----------|-----------|-----------|-----------------------|
| `app_id` (Release) | `page.kramo.Cartridges` | `page.samuelm333.Cartridges` | Production build |
| `app_id` (Development) | `page.kramo.Cartridges.Devel` | `page.samuelm333.Cartridges.Devel` | Development build |
| `prefix` (Release) | `/page/kramo/Cartridges` | `/page/samuelm333/Cartridges` | Production build |
| `prefix` (Development) | `/page/kramo/Cartridges/Devel` | `/page/samuelm333/Cartridges/Devel` | Development build |

---

## 2. GSettings Schema Model

The GSettings schemas define the application settings and UI state. They are dynamically parameterized via Meson.

### Primary Schema: `page.samuelm333.Cartridges`
- **Path**: `/page/samuelm333/Cartridges/`
- **Fields**:
  - `collections` (type: `aa{sv}`): Custom collections created by the user containing groups of games.
    - **Default**: `[]`

### State Schema: `page.samuelm333.Cartridges.State`
- **Path**: `/page/samuelm333/Cartridges/State/`
- **Fields**:
  - `width` (type: `i`): The window width in pixels.
    - **Default**: `920`
  - `height` (type: `i`): The window height in pixels.
    - **Default**: `700`
  - `is-maximized` (type: `b`): Whether the application window is maximized.
    - **Default**: `false`
  - `sort-mode` (type: `s`): The sorting order of the games grid.
    - **Choices**: `last_played`, `a-z`, `z-a`, `newest`, `oldest`
    - **Default**: `"last_played"`
  - `show-sidebar` (type: `b`): Whether the sidebar is shown.
    - **Default**: `false`

---

## 3. Desktop Entry Model

The generated desktop file defines the desktop environment launcher.

- **File Name**: `page.samuelm333.Cartridges.desktop` (release) or `page.samuelm333.Cartridges.Devel.desktop` (development)
- **Key Attributes**:
  - `Name`: `Cartridges` (Release) or `Cartridges (Devel)` (Development)
  - `Exec`: `cartridges`
  - `Icon`: `page.samuelm333.Cartridges` or `page.samuelm333.Cartridges.Devel`
  - `DBusActivatable`: `true`

---

## 4. D-Bus Service Model

The GIO Application utilizes D-Bus activation to manage window single-instance behaviors.

- **Service Name**: `page.samuelm333.Cartridges` (or `page.samuelm333.Cartridges.Devel`)
- **Service Path**: `data/page.samuelm333.Cartridges.service.in` (to be compiled to `page.samuelm333.Cartridges.service` or `page.samuelm333.Cartridges.Devel.service` respectively)

