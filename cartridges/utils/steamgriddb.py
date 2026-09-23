# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2022-2026 kramo

import json
import logging
import urllib.parse
from io import BytesIO
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cartridges import SETTINGS, cover
from cartridges.cover import COVERS_DIR

_logger = logging.getLogger(__name__)

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404

ERR_NO_KEY = "SteamGridDB API key is not configured"
ERR_INVALID_KEY = "Invalid SteamGridDB API key"


class SgdbError(Exception):
    """Base exception for SteamGridDB operations."""


class SgdbAuthError(SgdbError):
    """Authentication failed or API key missing/invalid."""


class SgdbGameNotFoundError(SgdbError):
    """Game was not found on SteamGridDB."""


class SgdbNoImageFoundError(SgdbError):
    """No matching cover image found."""


SgdbGameNotFound = SgdbGameNotFoundError
SgdbNoImageFound = SgdbNoImageFoundError


def _get_auth_headers() -> dict[str, str]:
    key = SETTINGS.get_string("sgdb-key").strip()
    if not key:
        msg = ERR_NO_KEY
        raise SgdbAuthError(msg)
    return {
        "Authorization": f"Bearer {key}",
        "User-Agent": "Cartridges/2.0",
    }


def get_game_id(game_name: str) -> int:
    """Get SteamGridDB game ID via autocomplete search."""
    headers = _get_auth_headers()
    quoted = urllib.parse.quote(game_name)
    url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{quoted}"
    _logger.info("Searching SteamGridDB ID for game: %s", game_name)
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=10) as res:
            if res.status == HTTP_OK:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("success") and data.get("data"):
                    sgdb_id = int(data["data"][0]["id"])
                    _logger.info("Found SteamGridDB ID %d for %s", sgdb_id, game_name)
                    return sgdb_id
                msg = f"Game '{game_name}' not found on SteamGridDB"
                raise SgdbGameNotFound(msg)
            if res.status == HTTP_UNAUTHORIZED:
                msg = ERR_INVALID_KEY
                raise SgdbAuthError(msg)
            msg = f"HTTP status {res.status}"
            raise SgdbError(msg)
    except HTTPError as e:
        if e.code == HTTP_UNAUTHORIZED:
            msg = ERR_INVALID_KEY
            raise SgdbAuthError(msg) from e
        if e.code == HTTP_NOT_FOUND:
            msg = f"Game '{game_name}' not found"
            raise SgdbGameNotFound(msg) from e
        msg = f"SteamGridDB search HTTP error: {e}"
        raise SgdbError(msg) from e
    except URLError as e:
        _logger.warning("Network error querying SteamGridDB for %s: %s", game_name, e)
        msg = f"Network error: {e}"
        raise SgdbError(msg) from e


def get_image_url(sgdb_id: int, animated: bool = False) -> str:
    """Get the first grid image URL for a game ID."""
    headers = _get_auth_headers()
    url = f"https://www.steamgriddb.com/api/v2/grids/game/{sgdb_id}?dimensions=600x900"
    if animated:
        url += "&types=animated"
    _logger.info(
        "Fetching cover URL for SteamGridDB ID %d (animated=%s)", sgdb_id, animated
    )
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=10) as res:
            if res.status == HTTP_OK:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("success") and data.get("data"):
                    img_url = str(data["data"][0]["url"])
                    _logger.info(
                        "Retrieved image URL for SGDB ID %d: %s", sgdb_id, img_url
                    )
                    return img_url
                msg = f"No image found for SGDB ID {sgdb_id}"
                raise SgdbNoImageFound(msg)
            if res.status == HTTP_UNAUTHORIZED:
                msg = ERR_INVALID_KEY
                raise SgdbAuthError(msg)
            msg = f"HTTP status {res.status}"
            raise SgdbError(msg)
    except HTTPError as e:
        if e.code == HTTP_UNAUTHORIZED:
            msg = ERR_INVALID_KEY
            raise SgdbAuthError(msg) from e
        if e.code == HTTP_NOT_FOUND:
            msg = f"No image found for SGDB ID {sgdb_id}"
            raise SgdbNoImageFound(msg) from e
        msg = f"SteamGridDB grid query HTTP error: {e}"
        raise SgdbError(msg) from e
    except URLError as e:
        _logger.warning("Network error querying grid covers for ID %d: %s", sgdb_id, e)
        msg = f"Network error: {e}"
        raise SgdbError(msg) from e


def get_grid_covers(sgdb_id: int) -> list[dict[str, Any]]:
    """Get grid cover art options for a game ID."""
    headers = _get_auth_headers()
    url = f"https://www.steamgriddb.com/api/v2/grids/game/{sgdb_id}?dimensions=600x900"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=10) as res:
            if res.status == HTTP_OK:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("success") and "data" in data:
                    return cast(list[dict[str, Any]], data["data"])
    except (HTTPError, URLError, TimeoutError) as e:
        _logger.warning("Failed to retrieve grid covers for SGDB ID %d: %s", sgdb_id, e)
    return []


def save_cover_from_url(game_id: str, url: str) -> bool:
    """Download, convert, resize, compress and save cover art to disk."""
    from PIL import Image, ImageSequence

    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    _logger.info("Downloading cover for game %s from %s", game_id, url)
    try:
        req = Request(url, headers={"User-Agent": "Cartridges/2.0"})
        with urlopen(req, timeout=15) as res:
            content = res.read()
    except (HTTPError, URLError, TimeoutError) as e:
        _logger.warning("Failed to download image from %s: %s", url, e)
        return False

    try:
        orig_backup = COVERS_DIR / f"{game_id}.orig.tiff"
        curr_tiff = COVERS_DIR / f"{game_id}.tiff"
        curr_gif = COVERS_DIR / f"{game_id}.gif"
        if not orig_backup.exists():
            import shutil

            if curr_tiff.exists():
                shutil.copyfile(curr_tiff, orig_backup)
            elif curr_gif.exists():
                shutil.copyfile(curr_gif, orig_backup)

        with Image.open(BytesIO(content)) as orig_img:
            is_animated = getattr(orig_img, "is_animated", False)
            if is_animated:
                frames = [
                    frame.resize((cover.WIDTH, cover.HEIGHT))
                    for frame in ImageSequence.Iterator(orig_img)
                ]
                dest_path = COVERS_DIR / f"{game_id}.gif"
                (COVERS_DIR / f"{game_id}.tiff").unlink(missing_ok=True)
                frames[0].save(
                    dest_path,
                    save_all=True,
                    append_images=frames[1:],
                )
                _logger.info("Saved animated cover for %s to %s", game_id, dest_path)
            else:
                proc_img = orig_img
                if proc_img.mode not in ("RGB", "RGBA"):
                    proc_img = proc_img.convert("RGBA")
                dest_path = COVERS_DIR / f"{game_id}.tiff"
                (COVERS_DIR / f"{game_id}.gif").unlink(missing_ok=True)

                high_quality = SETTINGS.get_boolean("high-quality-images")
                resized = proc_img.resize((cover.WIDTH, cover.HEIGHT))
                resized.save(
                    dest_path,
                    compression="tiff_adobe_deflate" if high_quality else "tiff_lzw",
                )
                _logger.info("Saved cover for %s to %s", game_id, dest_path)
            return True
    except OSError as e:
        _logger.warning("Failed to save cover image for %s: %s", game_id, e)
        return False
