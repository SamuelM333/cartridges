# Feature Specification: Debug Logs

**Feature Branch**: `feat/010-debug-logs`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "new feat: Debug logs toggle in settings. Add a toggle in settings to generate logs in the best place locally (xdg_data_home or similar). Files should rotate on size. Feature is available in all stages (release, nightly, dev)"

## Overview

Today Cartridges only writes its diagnostic messages to the terminal it was started from. Most users start the app from their desktop launcher, so those messages are lost, and when something goes wrong (a source imports nothing, a cover fails to download, a game will not launch) there is nothing to attach to a bug report.

This feature adds a "Debug Logs" switch to Preferences. When it is on, Cartridges writes detailed diagnostic messages to log files in the user's local application state folder. The files are rotated by size so they never grow without bound. The switch, and everything it does, is the same in every build of the app: release, nightly, and development.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Turn on debug logging to capture a problem (Priority: P1)

A user hits a problem, for example a source that imports no games. They open Preferences, turn on "Debug Logs", repeat the action that failed, and now have a log file on disk that records what the app did in detail.

**Why this priority**: This is the whole point of the feature. Without it, nothing else has value.

**Independent Test**: Turn the switch on, run an import, and confirm a log file exists in the expected folder and contains detailed messages about the import, with timestamps.

**Acceptance Scenarios**:

1. **Given** Debug Logs is off, **When** the user turns it on in Preferences, **Then** detailed messages start being written to a log file right away, without restarting the app.
2. **Given** Debug Logs is on, **When** the user runs an import, **Then** the log file contains timestamped messages from the import, including messages more detailed than what the terminal shows by default.
3. **Given** Debug Logs is on, **When** the user closes and reopens the app, **Then** logging is still on and messages from the new run are appended to the log (startup messages included).
4. **Given** Debug Logs is on, **When** the user turns it off, **Then** no further messages are written to the log files, and the existing files are left in place.
5. **Given** a fresh install, **When** the user opens Preferences, **Then** Debug Logs is off and no log files have been created.

---

### User Story 2 - Find the log files to share them (Priority: P2)

Having captured a problem, the user needs to find the log files to attach them to a bug report. From the same place in Preferences, they open the folder that holds the logs in their file manager.

**Why this priority**: Logs that cannot be found are almost as useless as no logs. However, a technical user can still find the folder by its documented location, so the feature works without this.

**Independent Test**: With at least one log file present, use the "open logs folder" control in Preferences and confirm the file manager opens on the folder containing the log files.

**Acceptance Scenarios**:

1. **Given** log files exist, **When** the user chooses to open the logs folder from Preferences, **Then** the system file manager opens showing the folder that contains the log files.
2. **Given** the app runs inside the Flatpak sandbox, **When** the user opens the logs folder, **Then** the folder opens in the host file manager.
3. **Given** no log file has ever been written, **When** the user chooses to open the logs folder, **Then** the folder is created if needed and opened (empty), rather than showing an error.

---

### User Story 3 - Logs never fill the disk (Priority: P2)

A user turns on Debug Logs and forgets about it. Months later, the logs still take up only a small, fixed amount of space.

**Why this priority**: Without a cap, a forgotten switch could slowly fill the user's disk, which would be a serious regression. It is P2 only because it matters after time passes, not on first use.

**Independent Test**: With logging on, generate enough activity to exceed the per-file size limit several times over, and confirm the total size of the log folder stays at or under the documented maximum and that the newest messages are always present.

**Acceptance Scenarios**:

1. **Given** Debug Logs is on and the current log file reaches the size limit, **When** the next message is written, **Then** the current file is moved aside as the most recent archived file and a new, empty current file is started.
2. **Given** the maximum number of archived files already exists, **When** the current file rotates again, **Then** the oldest archived file is deleted.
3. **Given** any amount of activity, **When** the user inspects the logs folder, **Then** its total size never exceeds the documented maximum.

---

### Edge Cases

- **Log folder cannot be created or written** (read-only disk, full disk, permissions): the app keeps working normally, nothing crashes, and the user is told once (in-app, non-blocking) that debug logs could not be written. The switch is not silently flipped back.
- **Log file deleted or moved while the app is running**: logging recovers by writing to a new file at the expected location, or at worst stops writing without affecting the app.
- **Sensitive data**: the SteamGridDB API key, and any other secret the app stores, must never appear in a log file, even at the most detailed level.
- **Several instances or rapid on/off toggling**: toggling on and off repeatedly must not produce duplicate lines or leave extra files open.
- **Terminal output**: turning Debug Logs on or off does not change what the app prints to the terminal.
- **Different builds installed side by side** (release, nightly, development): each build keeps its own logs and its own switch, so logs from different builds are never mixed in the same file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preferences MUST include a "Debug Logs" on/off switch, placed in the General page, with a short subtitle explaining that it saves detailed diagnostic messages to disk for troubleshooting.
- **FR-002**: The switch MUST be off by default.
- **FR-003**: The switch's state MUST be remembered across app restarts.
- **FR-004**: When the switch is on, the app MUST write diagnostic messages at the most detailed level to a log file; when it is off, the app MUST NOT write to log files.
- **FR-005**: Turning the switch on or off MUST take effect immediately, without restarting the app.
- **FR-006**: When the app starts with the switch already on, logging MUST begin early enough to capture startup messages, including the startup import.
- **FR-007**: Every log line MUST include the date and time (to at least the second), the severity level, and the part of the app that produced it.
- **FR-008**: The first lines written in each app run MUST identify the app version, the build type (release, nightly, or development), and whether the app runs inside Flatpak, so a log can be matched to the build that produced it.
- **FR-009**: Log files MUST be stored in the user's local per-application state folder, following the XDG Base Directory conventions (and the Flatpak equivalent when sandboxed), in a dedicated `logs` subfolder.
- **FR-010**: The current log file MUST be rotated once it reaches 1 MiB; up to 4 archived files MUST be kept, and older ones deleted, so the logs folder never exceeds 5 MiB in total.
- **FR-011**: Preferences MUST offer a way to open the logs folder in the system file manager, available whenever the Debug Logs switch is visible.
- **FR-012**: Turning the switch off MUST NOT delete existing log files.
- **FR-013**: Log files MUST NOT contain the SteamGridDB API key or any other stored credential.
- **FR-014**: Any failure to create or write the log files MUST NOT crash the app or interrupt the user's current action; the user MUST be notified once per run with a non-blocking in-app message.
- **FR-015**: The switch, its default, the log location rules, and the rotation limits MUST be identical in the release, nightly, and development builds.
- **FR-016**: Each build type MUST keep its own log files, separate from the other build types installed on the same system.
- **FR-017**: Enabling Debug Logs MUST NOT change what the app writes to the terminal.

### Key Entities

- **Debug Logs setting**: A single on/off preference, off by default, stored with the app's other preferences and kept per build type.
- **Log file set**: One current log file plus up to four archived files, in the per-build `logs` folder. Each file holds timestamped log lines, newest at the end; archived files are ordered from most to least recent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from "something went wrong" to "log file open in the file manager" in under 1 minute, using only Preferences.
- **SC-002**: With Debug Logs on, 100% of startup and import runs produce timestamped entries in the current log file.
- **SC-003**: Under continuous logging, the logs folder never exceeds 5 MiB.
- **SC-004**: Zero app crashes or blocked actions are caused by an unwritable log location.
- **SC-005**: Searching every log file for the stored SteamGridDB API key returns zero matches.
- **SC-006**: The same steps to enable and find logs work identically in release, nightly, and development builds.
- **SC-007**: With Debug Logs off (the default), no log files are created on disk.

## Assumptions

- "The best place locally" is interpreted as the XDG state folder (`$XDG_STATE_HOME`, by default `~/.local/state`) rather than the data folder, because the XDG Base Directory specification designates the state folder for logs. Inside Flatpak this resolves to the app's private state folder (`~/.var/app/<app id>/.local/state`). Separate app IDs for each build type give each build its own folder (FR-016).
- Rotation limits (1 MiB per file, 4 archived files, 5 MiB total) are chosen as a reasonable default for a desktop app: large enough to hold many runs of detail, small enough to attach to a bug report. They are not user-configurable.
- Logs are not removed automatically when the switch is turned off; the user can delete them from the opened folder. A "clear logs" control is out of scope.
- Log content is plain text in a single fixed format; there is no in-app log viewer, no log level picker, and no automatic upload or sharing.
- On platforms other than Linux (if the app is built for them), the platform's conventional per-user application state or log folder is used instead; the switch and rotation behave the same.
- Paths to game files, launchers, and the user's home folder may appear in logs. This is acceptable for a user-initiated, off-by-default troubleshooting feature whose files stay on the user's machine; credentials are always excluded (FR-013).
