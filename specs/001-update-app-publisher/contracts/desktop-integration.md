# Desktop Integration Interface Contracts

This document specifies the system interface contracts between Cartridges, the Flatpak sandbox host, and the desktop environment shell (D-Bus / GSettings / Desktop Launchers).

## 1. D-Bus Service Contract

GNOME Shell and Flatpak require the application's reverse-DNS ID to match its D-Bus service name exactly to enable D-Bus activation and system shell integration.

- **Bus Name**: `page.samuelm333.Cartridges`
- **Object Path**: `/page/samuelm333/Cartridges`
- **Interface**: `org.freedesktop.Application`
- **Behavior**: System MUST launch the app via D-Bus activation when the desktop launcher is clicked. The application MUST register on the Session Bus under this exact name.

---

## 2. GSettings Schema Contract

To read and write settings, the application must load and utilize the GSettings schema registered under the exact application ID.

- **Schema ID**: `page.samuelm333.Cartridges`
- **State Schema ID**: `page.samuelm333.Cartridges.State`
- **Path Boundary**: `/page/samuelm333/Cartridges/` and `/page/samuelm333/Cartridges/State/`
- **Sandbox Requirement**: The Flatpak sandbox will automatically grant read/write access to this schema ID namespace on the host machine. Attempting to use any other namespace will cause permission errors.

---

## 3. Desktop Entry Contract

The desktop entry tells the window manager how to launch the application and associate its window with the correct icon and name.

- **Desktop File**: `page.samuelm333.Cartridges.desktop`
- **Window Class (`WM_CLASS`)**: `page.samuelm333.Cartridges`
- **Icon Association**: The window manager matches the window's `WM_CLASS` property (which must be `page.samuelm333.Cartridges`) to the desktop entry file name and icon file prefix to render the high-resolution app icon in the task bar and app grid.
