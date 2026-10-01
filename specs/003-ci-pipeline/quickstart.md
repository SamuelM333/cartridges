# Quickstart Validation Guide: Linux/Flatpak CI Pipeline & Workflows

## 1. Overview
This guide provides verification procedures for local syntax and workflow simulation to validate that GitHub Actions workflows, Flatpak manifests, and packaging templates function properly before pushing.

## 2. Prerequisites
- `distrobox enter gtk-dev` with `uv`, `pre-commit`, `meson`, `ninja`, and `blueprint-compiler`.
- Python 3.13+ installed in environment.

## 3. Validation Scenarios

### Scenario A: Local Pre-Commit & Code Quality Verification
Prove that repository files comply with all pre-commit hooks configured for CI:
```bash
distrobox enter gtk-dev -- uv run pre-commit run --all-files
```
**Expected Outcome**: All hooks (ruff-check, ruff-format, pyright, blueprint, meson, prettier, svgo, EOF, whitespace) pass without errors.

### Scenario B: Zero Emoji Integrity Gate
Prove that no emoji characters are present across workflows or docs:
```bash
python3 .specify/scripts/bash/check-emojis.py
```
**Expected Outcome**: Output indicates `Zero emojis found in diff!`.

### Scenario C: Production & Devel Flatpak Manifest Validation
Verify that both JSON Flatpak manifests are syntactically valid JSON:
```bash
python3 -c "import json; [json.load(open(f)) for f in ['flatpak/page.samuelm333.Cartridges.Devel.json', 'flatpak/page.samuelm333.Cartridges.json']]; print('Flatpak manifests valid JSON')"
```
**Expected Outcome**: Manifest files parse successfully without JSON syntax exceptions.

### Scenario D: Release Notes Extraction Simulation
Verify that the release note extraction logic cleanly extracts release notes from AppStream metadata:
```bash
python3 -c "
import re, textwrap
with open('data/page.samuelm333.Cartridges.metainfo.xml.in', encoding='utf-8') as f:
    content = f.read()
match = re.search(r'<release[^>]*>\s*<description[^>]*>\n([\s\S]*?)\s*</description>\s*</release>', content)
notes = textwrap.dedent(match.group(1)) if match else 'No notes'
print('Extracted:', notes)
"
```
**Expected Outcome**: Successfully extracts the description text without XML parsing errors.

### Scenario E: Nightly Cache Deduplication Logic Verification
Verify that the cache key generation and sentinel logic function in a local shell script simulation:
```bash
python3 -c "
import subprocess
sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
cache_key = f'nightly-built-{sha}'
assert len(sha) == 40
print(f'Computed cache key: {cache_key}')
"
```
**Expected Outcome**: Prints `Computed cache key: nightly-built-<sha>` with valid 40-character hex hash.
