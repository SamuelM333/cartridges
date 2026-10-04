# Data Model: SteamGridDB Cover Picker and Credentials UX

**Feature**: SteamGridDB Cover Picker and Credentials UX
**Branch**: `004-steamgriddb-picker`
**Date**: 2026-10-03

## 1. Entities & Data Models

### 1.1 Cover Candidate (`CoverCandidate`)
Represents an artwork candidate returned from SteamGridDB.

| Field | Type | Description |
|-------|------|-------------|
| `full_url` | `str` | High-resolution image URL to download if selected |
| `thumb_url` | `str` | Thumbnail or preview image URL for chooser display |
| `is_animated` | `bool` | Flag indicating whether the asset is an animated GIF |
| `score` | `int` | Upvote/quality rating from SteamGridDB |
| `author` | `str` | Creator/artist attribution name |

#### Validation & Constraints
- `full_url` and `thumb_url` must be valid HTTP/HTTPS URLs.
- If `thumb_url` is absent or empty in API response, defaults to `full_url`.

---

### 1.2 Preview Cache Entry (`PreviewCacheEntry`)
Represents a cached preview image file stored on disk.

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | SHA-256 hash of the `thumb_url` |
| `path` | `Path` | Filesystem path under `$XDG_CACHE_HOME/cartridges/previews/` |
| `timestamp` | `float` | POSIX timestamp of file creation or last access |
| `data` | `bytes` | Binary image payload |

#### Lifecycle Rules
- **Cache Hit**: File exists at `path` and `(current_time - timestamp) < TTL_SECONDS` (default: 7 days).
- **Cache Miss**: File does not exist or has expired. Download from network, write to `path`, update `mtime`.
- **Eviction / Pruning**: Files with `(current_time - timestamp) >= TTL_SECONDS` are deleted during periodic or startup pruning.
- **Session Cleanup**: Files flagged as transient are removed on application shutdown (`do_shutdown`).

---

### 1.3 SteamGridDB Key Credential Setting
Stored in the application's GSettings schema (`page.samuelm333.Cartridges`).

| Key Name | Type | Default | Description |
|----------|------|---------|-------------|
| `sgdb-key` | `s` (string) | `""` | User's SteamGridDB API key |

#### UI Presentation State (`Adw.PasswordEntryRow`)
- **Masked Mode**: Characters rendered as obscuring bullets/dots (default).
- **Revealed Mode**: Plaintext characters visible when the eye icon is toggled active.
- Underlying stored value in GSettings remains identical in both presentation modes.

---

### 1.4 Cover Picker UI State (`CoverPickerState`)
State machine managing the chooser dialog presentation.

```
       [Open Dialog]
             │
             ▼
      ┌──────────────┐
      │   LOADING    │  Initial centered spinner active
      └──────┬───────┘
             │
             ├──────────────────────────┐
             │                          │
      [1st batch ready]         [No results / Error]
             │                          │
             ▼                          ▼
      ┌──────────────┐           ┌──────────────┐
      │   RESULTS    │           │    EMPTY     │
      │ (with bottom │           │ Status page  │
      │   spinner)   │           │ with message │
      └──────┬───────┘           └──────────────┘
             │
      [All batches complete]
             │
             ▼
      ┌──────────────┐
      │   RESULTS    │
      │ (bottom      │
      │ spinner off) │
      └──────────────┘
```

#### State Transition Details
1. **Initial**: `stack.set_visible_child_name("loading")`, `initial_spinner.start()`.
2. **First Batch Rendered**: `stack.set_visible_child_name("results")`. If additional items exist to fetch, `bottom_spinner.set_visible(True)`.
3. **All Candidates Loaded**: `bottom_spinner.set_visible(False)`.
4. **No Candidates / Search Error**: `stack.set_visible_child_name("empty")`, display `Adw.StatusPage`.

---

### 1.5 Game Details Cover Overlay Staging State (`CoverStagingState`)
*Status: Already implemented in `cartridges/ui/game_details.py`.*

| Property | Type | Description |
|----------|------|-------------|
| `cover_loading` | `bool` | GObject boolean property controlling the centered loading spinner overlay in the Game Details cover view. Set to `True` during asynchronous cover download/processing, reset to `False` on completion, error, cancel, or apply. |
| `name_entry` error state | `bool` | CSS class `"error"` dynamically added to `name_entry` when SteamGridDB search is triggered with an empty title, cleared as soon as characters are entered. |
