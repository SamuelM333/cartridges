# Feature Specification: Update App Publisher Metadata

**Feature Branch**: `001-update-app-publisher`

**Created**: 2026-09-21

**Status**: Ready for Planning

**Input**: User description: "I want to update the project metadata to replace the publisher of the app, from kramo to samuelm333, and update the Flatpak FQN (Application ID) to page.samuelm333.Cartridges. Only replace metadata relevant with publishing, without scrubbing away historical developer contributions or previous author's attribution (kramo)."

## Clarifications

### Session 2026-09-21

- Q: Are "Jamie, Laura, Zoey" the actual previous authors to preserve, or are they placeholders? → A: They are placeholders; the actual previous author/maintainer to preserve is "kramo".
- Q: Should the app support out-of-the-box Flatpak building inside GNOME Builder? → A: Yes, the Flatpak manifest and directory layout must support seamless, out-of-the-box building in GNOME Builder.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Publisher in Software Center (Priority: P1)

As a user searching for the app in a Linux Software Center (e.g., GNOME Software or Flathub), I want to see "samuelm333" listed as the developer/publisher of Cartridges so that I know who publishes and maintains the app.

**Why this priority**: Correct public developer attribution and branding is essential for user trust and discoverability.

**Independent Test**: Can be verified by validating the compiled metainfo.xml file with the `appstreamcli validate` or `appstream-util validate` tool to ensure the developer and publisher fields are correctly parsed.

**Acceptance Scenarios**:

1. **Given** the AppStream metadata file, **When** compiled and inspected, **Then** the developer ID must match the new publisher "page.samuelm333".
2. **Given** the about dialog in the application, **When** opened by a user, **Then** the current publisher/developer attribution must display "samuelm333" while retaining the name and credit of the previous author ("kramo") so that historical contributions are preserved.

---

### User Story 2 - Access Project & Support Links (Priority: P2)

As an app user or contributor, I want to access the correct repository and support URLs from the app's metadata or Software Center page so that I can report issues, contribute code, or view project files under the new publisher's home.

**Why this priority**: Keeps the feedback loop active and directs contributors/users to the correct, active project repository.

**Independent Test**: Can be verified by clicking the project, issue tracker, and contribution links within the Software Center or about dialog and ensuring they point to the correct URL paths.

**Acceptance Scenarios**:

1. **Given** the AppStream metainfo URLs, **When** checked, **Then** all VCS, bugtracker, and contribution links point to the updated publisher's repository.

---

### User Story 3 - Install and Launch App under New Application ID (Priority: P2)

As a user installing Cartridges from a Flatpak repository or software manager, I want the application to be correctly registered under the publisher's reverse-DNS namespace (`page.samuelm333.Cartridges`) so that it conforms to Flatpak publishing guidelines and does not conflict with legacy installations.

**Why this priority**: Proper application namespacing is mandatory for publishing on modern Flatpak repositories like Flathub under a personal domain/organization.

**Independent Test**: Can be verified by installing the packaged Flatpak and checking that it runs under the application ID `page.samuelm333.Cartridges` (or `page.samuelm333.Cartridges.Devel` for development builds).

**Acceptance Scenarios**:

1. **Given** a built Flatpak package, **When** inspected, **Then** the App ID/FQN is `page.samuelm333.Cartridges` or `page.samuelm333.Cartridges.Devel`.
2. **Given** the application is running, **When** DBus or desktop launcher environments inspect the active window, **Then** the window class and DBus name match the new Application ID.

---

### Edge Cases

- **Backward Compatibility of Application ID**: Since the Application ID is updated to `page.samuelm333.Cartridges`, previous user settings (GSettings), cached game covers, and launcher configurations saved in the old namespaces will not load automatically. An upgrade/migration path is not planned for local configurations, but the AppStream metainfo should contain `<replaces>` tags for `hu.kramo.Cartridges` and `page.kramo.Cartridges` to assist software centers with migration.
- **Translatability of Metadata**: The translation template (`.pot` / `.po` files) must be synchronized so translators can localize the updated developer name if necessary, or ensure that names are marked correctly as untranslatable where appropriate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST update the AppStream metainfo file developer ID to reference "page.samuelm333" as the developer/publisher ID instead of "page.kramo".
- **FR-002**: System MUST update developer-related repository URLs (VCS-browser, bugtracker, contribute) to point to the new publisher's host domain.
- **FR-003**: System MUST update the developer ID field in the AppStream metainfo file to match the new publisher namespace.
- **FR-004**: System MUST update the Flatpak FQN / Application ID to `page.samuelm333.Cartridges` (and `page.samuelm333.Cartridges.Devel` for development builds) across all configuration, source, and build files.
- **FR-005**: System MUST point all VCS-browser, bugtracker, and contribution links to `https://github.com/samuelm333/cartridges` and its corresponding sub-pages.
- **FR-006**: System MUST rename all files in the repository prefixed with `page.kramo.Cartridges` to use `page.samuelm333.Cartridges`.
- **FR-007**: System MUST update D-Bus service, GSettings schemas, and application source code references to use the new Application ID.
- **FR-008**: System MUST ensure that the legacy Application IDs (`page.kramo.Cartridges`, `page.kramo.Cartridges.Devel`, `hu.kramo.Cartridges`, and `hu.kramo.Cartridges.Devel`) are blacklisted within the application's desktop game source so they do not show up as importable games.
- **FR-009**: System MUST NOT remove previous author ("kramo") from the application's About Dialog or user-facing attribution, keeping them listed as the primary historical developer/author.
- **FR-010**: System MUST ensure only metadata relevant with publishing is updated, keeping code copyright headers and historical author/developer attributions intact throughout the codebase.
- **FR-011**: The application build setup and Flatpak manifest MUST be compatible with GNOME Builder out-of-the-box, allowing developer imports, compilation, and execution without additional manual configuration.

### Key Entities

- **AppStream Metainfo**: The XML/JSON document defining store metadata, screenshots, urls, developer name, and translation sources for desktop storefronts.
- **Application ID / D-Bus Name**: The unique reverse-DNS identifier used by Flatpak, GNOME Shell, GSettings, and D-Bus to identify and sandbox the app, now updated to `page.samuelm333.Cartridges`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of AppStream validator checks (`appstreamcli validate` or equivalent) pass with zero errors or warnings regarding developer/developer_id tags and application IDs.
- **SC-002**: 100% of developer metadata links (VCS, bug tracker, contribute) point to active, reachable URLs matching the new publisher.
- **SC-003**: Desktop shell launcher, GNOME Software integration, and desktop files build and compile with zero errors using the updated definitions.
- **SC-004**: 100% of compiled resource and desktop files are successfully generated with the new Application ID.
- **SC-005**: No instances of the old ID `page.kramo.Cartridges` remain in active build or runtime configurations, except where necessary for backward-compatible reference (e.g., AppStream `<replaces>` tag or legacy game source blacklisting).

## Assumptions

- **A-001**: The license and copyright information (e.g., SPDX copyright headers in source files) are distinct from publisher/developer metadata; files will retain their historical copyright headers unless explicitly requested otherwise.
- **A-002**: Standard GNOME Adwaita and Flatpak conventions are followed when specifying developer metadata.
- **A-003**: Updating the Application ID to `page.samuelm333.Cartridges` requires changing D-Bus and GSettings paths, which means prior settings and caches under the old namespaces will be reset for existing users.
