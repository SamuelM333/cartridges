# Data Model: Debug Logs

**Feature**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Debug Logs setting

| Field | Store | Type | Default | Notes |
|-------|-------|------|---------|-------|
| `debug-logs` | GSettings, main schema `@APP_ID@` | `b` | `false` | Per build (each profile has its own schema ID). Reset by "Reset App" like other keys. |

**Transitions**:

```text
off --(user turns switch on)--> on : attach file handler, write run header
on  --(user turns switch off)--> off : detach and close handler; files kept
on  --(app starts)-----------------> on : attach before Application is created
on  --(write fails)----------------> on (handler detached for this run) : one toast; switch unchanged
```

## Log file set

Location: `<XDG state dir>/cartridges/logs/` (see [research.md](research.md) R1, R2).

| File | Role |
|------|------|
| `<APP_ID>.log` | Current file; new records are appended. |
| `<APP_ID>.log.1` | Most recent archive. |
| `<APP_ID>.log.2` .. `.log.4` | Older archives; `.log.4` is deleted on the next rotation. |

**Validation rules**:

- Current file rotates once writing the next record would exceed 1,048,576 bytes.
- At most 4 archives; the folder holds at most 5 files per app ID (about 5 MiB).
- Encoding is UTF-8; one record per line, except tracebacks, which follow their record.

## Log line

Format (see [contracts/log-file.md](contracts/log-file.md)):

```text
YYYY-MM-DD HH:MM:SS,mmm [LEVEL] logger.name: message
```

| Part | Source |
|------|--------|
| Timestamp | Local time, date and milliseconds (FR-007). |
| Level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| Logger name | The emitting module, e.g. `cartridges.importer`. |
| Message | After redaction of the stored SteamGridDB key (FR-013). |

## Build information (config)

| Name | Source | Values |
|------|--------|--------|
| `VERSION` | The `tag` meson option; else `development` for a development build; else `meson.project_version()` | `v1.2.3` (release), `nightly-abc1234` (nightly), `development`, or e.g. `49.0` (build from source without a tag) |
