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
Represents a rolling pre-release build of the development tip on `main`.
- **Attributes**:
  - `name`: String filename (`page.samuelm333.Cartridges.Devel.flatpak`).
  - `release_tag`: Constant `nightly`.
  - `commit_sha`: 40-character hex git commit hash of HEAD on `main`.
  - `build_timestamp`: ISO 8601 UTC timestamp.
  - `prerelease`: Boolean `true`.

### Entity: PR Flatpak Artifact
Represents a downloadable preview development build uploaded to GitHub Actions workflow artifacts during PR and branch validation.
- **Attributes**:
  - `name`: String artifact name (`page.samuelm333.Cartridges.Devel.flatpak`).
  - `path`: String bundle path (`page.samuelm333.Cartridges.Devel.flatpak`).
  - `workflow`: Workflow name (`CI`).
  - `commit_sha`: Git commit hash of the pull request or pushed commit.
- **Validation Rules**:
  - Must compile against `flatpak/page.samuelm333.Cartridges.Devel.json` without errors.
  - File size must be greater than zero.

### Entity: Nightly Cache Flag
Represents the deduplication state stored within GitHub Actions Cache.
- **Attributes**:
  - `cache_key`: Formatted string `nightly-built-${{ github.sha }}`.
  - `cache_path`: Local sentinel file `.nightly-flag`.
  - `hit`: Boolean indicating if current commit has already been processed.

## 2. State Transitions & Lifecycle

### Nightly Build Evaluation Lifecycle

1. **Trigger**: Scheduled daily cron (`0 2 * * *`) or manual dispatch (`workflow_dispatch`).
2. **Check Cache Key**: Look up `nightly-built-${{ sha }}` in `actions/cache`.
3. **Branch Decision**:
   - **Cache Hit**: Exit cleanly with success (skip building and publishing).
   - **Cache Miss**:
     - Compile development Flatpak bundle (`page.samuelm333.Cartridges.Devel.flatpak`).
     - Publish bundle to GitHub Release (tag: `nightly`).
     - Create sentinel file and save `nightly-built-${{ sha }}` to `actions/cache`.

### Production Release Lifecycle

1. **Trigger**: Push git tag matching `v*`.
2. **Build Flatpak**: Compile production bundle `page.samuelm333.Cartridges.flatpak` via `flatpak-builder`.
3. **Extract Release Notes**: Parse version changelog description from `data/page.samuelm333.Cartridges.metainfo.xml.in`.
4. **Publish GitHub Release**: Attach Flatpak bundle asset and publish release notes.
