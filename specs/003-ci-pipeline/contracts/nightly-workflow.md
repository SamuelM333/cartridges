# Contract: Nightly Build Workflow (`nightly.yml`)

## 1. Triggers & Inputs
- **Schedule**: Cron expression `0 2 * * *` (daily at 02:00 UTC).
- **Manual Dispatch**: `workflow_dispatch` with optional boolean force input:
  - `force`: Boolean (default `false`) - Force build even if commit was already cached.

## 2. Concurrency & Permissions
- **Concurrency**:
  ```yaml
  concurrency:
    group: nightly-${{ github.ref }}
    cancel-in-progress: false
  ```
- **Permissions**:
  ```yaml
  permissions:
    contents: write
  ```

## 3. Cache Contract
- **Cache Action**: `actions/cache@v4`
- **Cache Key**: `nightly-built-${{ github.sha }}`
- **Path**: `.nightly-flag`

### Step Outputs:
- `cache-hit`: `'true'` if cache key exists; `'false'` or empty if not.

## 4. Output Artifacts
- **Release Target**: GitHub Release tagged `nightly`.
- **Assets**:
  - `page.samuelm333.Cartridges.Devel.flatpak`
- **Title**: `Nightly Build (${{ github.sha }})`
- **Body**: Automatically generated summary referencing the commit SHA and build timestamp.
- **Prerelease**: `true`
