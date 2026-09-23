# Tasks: Update App Publisher Metadata

This document defines the complete checklist of development, configuration, and verification tasks for implementing the publisher and Flatpak FQN / Application ID migration.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development environment prerequisites and branch status

- [x] T001 Confirm compilation and test verification tools are accessible inside the `gtk-dev` Distrobox container
- [x] T002 Verify git is on the correct branch `001-update-app-publisher` opened from `rewrite`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the new FQN/Application ID and prefix settings in the main build script

**CRITICAL**: No user story implementation or file renaming should begin until this build parameter is configured

- [x] T003 Modify `meson.build` to define the main application ID as `page.samuelm333.Cartridges` and the D-Bus/GSettings prefix as `/page/samuelm333/Cartridges` (with development profile suffixing `.Devel`)

**Checkpoint**: Foundation ready - main build variables updated

---

## Phase 3: User Story 1 - View Publisher in Software Center (Priority: P1) MVP

**Goal**: Update the AppStream metadata file with the new developer and publisher identities while preserving the historical author credit

**Independent Test**: Build and run `meson test -C _build` to verify that `appstreamcli validate` parses the metainfo file with 100% success

### Implementation for User Story 1

- [x] T004 [P] [US1] Create `data/page.samuelm333.Cartridges.metainfo.xml.in` from the legacy `data/page.kramo.Cartridges.metainfo.xml.in` template
- [x] T005 [P] [US1] Update the developer name to "samuelm333" and the developer ID to `page.samuelm333` inside `data/page.samuelm333.Cartridges.metainfo.xml.in`
- [x] T006 [P] [US1] Add the `<replaces>` block targeting `hu.kramo.Cartridges` and `page.kramo.Cartridges` inside `data/page.samuelm333.Cartridges.metainfo.xml.in`
- [x] T007 [P] [US1] Verify that the original author credit for "kramo" is cleanly preserved in `data/page.samuelm333.Cartridges.metainfo.xml.in`
- [x] T008 [US1] Delete the obsolete legacy file `data/page.kramo.Cartridges.metainfo.xml.in`

**Checkpoint**: User Story 1 is fully functional and ready for AppStream validation

---

## Phase 4: User Story 2 - Access Project & Support Links (Priority: P2)

**Goal**: Align all AppStream storefront and help links to point to the active GitHub fork repository

**Independent Test**: Clicking the VCS, Bug Tracker, and Contribution links in the built desktop storefront validates they point to Samuel's GitHub URL

### Implementation for User Story 2

- [x] T009 [P] [US2] Update homepage, bugtracker, VCS-browser, and contribution links to point to `https://github.com/samuelm333/cartridges` and its sub-pages inside `data/page.samuelm333.Cartridges.metainfo.xml.in`

**Checkpoint**: Store metadata and support links successfully redirect to the active GitHub repository

---

## Phase 5: User Story 3 - Install and Launch App under New Application ID (Priority: P2)

**Goal**: Migrate desktop entry templates, GSettings schemas, D-Bus service targets, Flatpak development manifests, and system icons to the new reverse-DNS namespace, and configure blacklist parameters to prevent self-importation

**Independent Test**: The app compiles, tests pass, and Cartridges correctly blacklists itself when scanning desktop launchers

### Implementation for User Story 3

- [x] T010 [P] [US3] Create `data/page.samuelm333.Cartridges.desktop.in` from `data/page.kramo.Cartridges.desktop.in`
- [x] T011 [P] [US3] Create `data/page.samuelm333.Cartridges.gschema.xml.in` from `data/page.kramo.Cartridges.gschema.xml.in`
- [x] T012 [P] [US3] Create `data/page.samuelm333.Cartridges.service.in` from `data/page.kramo.Cartridges.service.in`
- [x] T013 [P] [US3] Rename the four icon SVG files in `data/icons/` from `page.kramo.Cartridges*` to `page.samuelm333.Cartridges*`
- [x] T014 [P] [US3] Create `flatpak/page.samuelm333.Cartridges.Devel.json` from `flatpak/page.kramo.Cartridges.Devel.json`
- [x] T015 [P] [US3] Update application ID, file paths, and module parameters to `page.samuelm333.Cartridges.Devel` inside `flatpak/page.samuelm333.Cartridges.Devel.json`
- [x] T016 [US3] Delete deprecated files: `data/page.kramo.Cartridges.desktop.in`, `data/page.kramo.Cartridges.gschema.xml.in`, `data/page.kramo.Cartridges.service.in`, `data/icons/page.kramo.Cartridges*`, and `flatpak/page.kramo.Cartridges.Devel.json`
- [x] T017 [US3] Update `data/meson.build` to reference the renamed desktop, schema, metainfo, and service configuration files
- [x] T018 [US3] Update the translation resource list `po/POTFILES.in` with the renamed desktop and metainfo file paths
- [x] T019 [US3] Modify `cartridges/sources/desktop.py` to add `page.samuelm333.Cartridges` and `page.samuelm333.Cartridges.Devel` patterns to both `_FILE_BLACKLIST` and `_FLATPAK_ID_BLACKLIST`

**Checkpoint**: Core namespacing migration and file-level renaming completed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: General codebase adjustments, repository logo alignment, and comprehensive validation checks

- [x] T020 [P] Update the logo asset path inside `README.md` to reference `data/icons/page.samuelm333.Cartridges.svg`
- [x] T021 Validate build compilation inside the `gtk-dev` Distrobox container using `meson compile -C _build`
- [x] T022 Run the complete automated validation test suite using `meson test -C _build` inside the `gtk-dev` Distrobox container
- [x] T023 Run manual verification to confirm that GSettings schemas, About Dialog credits, and self-blacklisting function correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can be done immediately.
- **Foundational (Phase 2)**: Depends on Phase 1. BLOCKS all subsequent user stories.
- **User Stories (Phase 3-5)**: All depend on Phase 2 completion. These can technically run in parallel or sequentially.
- **Polish (Phase 6)**: Depends on all user story migrations being complete.

### Parallel Opportunities

- Within **Phase 3 (US1)**: Tasks T004, T005, T006, T007 modify different sections of the new metainfo template or prepare assets and can be performed in parallel.
- Within **Phase 5 (US3)**: Tasks T010, T011, T012, T013, T014, T015 target distinct system files, manifests, and graphics and can be developed simultaneously.
- Within **Phase 6**: T020 (documentation link updates) can be executed in parallel with any cleanups.

---

## Parallel Example: User Story 3

```bash
# Work on creating and setting up the new desktop entry, gschema, and D-Bus services concurrently:
Task: "Create data/page.samuelm333.Cartridges.desktop.in from data/page.kramo.Cartridges.desktop.in"
Task: "Create data/page.samuelm333.Cartridges.gschema.xml.in from data/page.kramo.Cartridges.gschema.xml.in"
Task: "Create data/page.samuelm333.Cartridges.service.in from data/page.kramo.Cartridges.service.in"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2 Only)

1. Run Phase 1 validation checks.
2. Complete Phase 2 build variable updates.
3. Complete Phase 3 (AppStream metainfo migration) and Phase 4 (Link updates).
4. Run `appstreamcli validate` to ensure publisher properties are correctly updated.

### Full Namespace Transition

1. Complete Phase 5 to fully rename and migrate desktop integration configurations, flatpak development manifests, and icon resources.
2. Complete build adjustments (`data/meson.build` and `po/POTFILES.in`).
3. Run Phase 6 checks inside the `gtk-dev` Distrobox container to verify 100% automated test compliance.
