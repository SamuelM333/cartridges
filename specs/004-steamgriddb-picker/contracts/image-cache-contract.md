# Contract: Preview Image Cache Interface

**Module**: `cartridges.utils.steamgriddb` (or `cartridges.utils.cache`)
**Storage Path**: `$XDG_CACHE_HOME/cartridges/previews/`

## 1. Storage & Path Conventions

- Cache directory: `Path(GLib.get_user_cache_dir(), "cartridges", "previews")`
- File naming: `hashlib.sha256(url.encode("utf-8")).hexdigest()` with `.bin` or image extension.
- Default expiration TTL: 7 days (`604800` seconds).

## 2. Functions Specification

```python
def get_cached_preview(url: str, max_age_seconds: int = 604800) -> bytes | None:
    """Retrieve cached preview image bytes if present and unexpired.

    Args:
        url: The remote thumbnail URL.
        max_age_seconds: Maximum allowed age in seconds before considering expired.

    Returns:
        Image bytes if cache hit and valid, otherwise None.
    """
    ...


def save_cached_preview(url: str, data: bytes) -> Path | None:
    """Persist downloaded preview image bytes to local cache directory.

    Args:
        url: The remote thumbnail URL.
        data: Raw image bytes to cache.

    Returns:
        Path to the saved cache file, or None on failure.
    """
    ...


def prune_expired_previews(max_age_seconds: int = 604800) -> int:
    """Scan the preview cache directory and delete files exceeding max_age_seconds.

    Returns:
        Number of evicted cache files.
    """
    ...


def clear_preview_cache() -> int:
    """Purge all temporary preview cache files.

    Invoked on application shutdown (`do_shutdown`) or when cache reset is requested.

    Returns:
        Number of deleted cache files.
    """
    ...
```

## 3. Network Fetching Integration

When fetching preview thumbnails:
1. Call `get_cached_preview(thumb_url)`.
2. If hit, return cached bytes immediately without network round-trip.
3. If miss, fetch over HTTP via background worker thread, call `save_cached_preview(thumb_url, data)`, and return bytes.
