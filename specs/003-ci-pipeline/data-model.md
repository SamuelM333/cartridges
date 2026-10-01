# Data Model & State Transitions: Linux/Flatpak CI Pipeline & Artifact Management

## 1. Entities & Specifications

### Entity: Release Flatpak Artifact
Represents an official immutable release asset attached to a GitHub Release.
- **Attributes**:
  - `name`: String filename (`page.samuelm333.Cartridges.flatpak`).
  - `tag_name`: String semantic tag matching `v[0-9]+.[0-9]+.[0-9]+`.
  - `commit_sha`: String 40-character hex git commit hash.
  - `content_type`: MIME type `application/vnd.flatpak`.
  - `release_notes`: Extracted AppStream description text.
- **Validation Rules**:
  - Must compile against `flatpak/page.samuelm333.Cartridges.json` without errors.
  - File size must be greater than zero.

### Entity: Nightly Flatpak Artifact
Represents a rolling pre-release build of the development tip on `rewrite`.
- **Attributes**:
  - `name`: String filename (`page.samuelm333.Cartridges.Devel.flatpak`).
  - `release_tag`: Constant `nightly`.
  - `commit_sha`: 40-character hex git commit hash of HEAD on `rewrite`.
  - `build_timestamp`: ISO 8601 UTC timestamp.
  - `prerelease`: Boolean `true`.

### Entity: Nightly Cache Flag
Represents the deduplication state stored within GitHub Actions Cache.
- **Attributes**:
  - `cache_key`: Formatted string `nightly-built-${{ github.sha }}`.
  - `cache_path`: Local sentinel file `.nightly-flag`.
  - `hit`: Boolean indicating if current commit has already been processed.

## 2. State Transitions & Lifecycle

### Nightly Build Evaluation Lifecycle

```
[Trigger (Cron / Dispatch)]
            |
            v
   [Check Cache Key]
    nightly-built-${{ sha }}
            |
    +-------+-------+
    |               |
[Cache Hit]    [Cache Miss]
    |               |
    v               v
 [Exit 0]     [Build Flatpak Bundle]
 (Skip Build) (page.samuelm333.Cartridges.Devel)
                    |
                    v
              [Upload to Release]
              (tag: nightly)
                    |
                    v
              [Save Cache Key]
                    |
                    v
                 [Done]
```

### Production Release Lifecycle

```
[Push Git Tag (v*)]
         |
         v
   [Build Flatpak]
(page.samuelm333.Cartridges.flatpak)
         |
         v
   [Extract Release Notes]
(from metainfo.xml.in)
         |
         v
   [Publish GitHub Release]
 (Attach Flatpak Bundle)
```
