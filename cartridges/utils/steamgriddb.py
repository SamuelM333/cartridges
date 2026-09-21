# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2022-2026 kramo

import json
import logging
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from cartridges import SETTINGS, cover
from cartridges.cover import COVERS_DIR


class SgdbError(Exception):
    pass


class SgdbAuthError(SgdbError):
    pass


class SgdbGameNotFound(SgdbError):
    pass


class SgdbNoImageFound(SgdbError):
    pass


def _get_auth_headers() -> dict[str, str]:
    key = SETTINGS.get_string("sgdb-key")
    return {
        "Authorization": f"Bearer {key}",
        "User-Agent": "Cartridges/2.0",
    }


def get_game_id(game_name: str) -> int:
    """Get SteamGridDB game ID via autocomplete search."""
    import urllib.parse

    headers = _get_auth_headers()
    url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{urllib.parse.quote(game_name)}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=5) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("success") and data.get("data"):
                    return int(data["data"][0]["id"])
                raise SgdbGameNotFound()
            elif res.status == 401:
                raise SgdbAuthError()
            else:
                raise SgdbError()
    except Exception as e:
        if "401" in str(e):
            raise SgdbAuthError()
        elif "404" in str(e):
            raise SgdbGameNotFound()
        raise SgdbError(str(e))


def get_image_url(sgdb_id: int, animated: bool = False) -> str:
    """Get the first grid image URL for a game ID."""
    headers = _get_auth_headers()
    url = f"https://www.steamgriddb.com/api/v2/grids/game/{sgdb_id}?dimensions=600x900"
    if animated:
        url += "&types=animated"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=5) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                if data.get("success") and data.get("data"):
                    return str(data["data"][0]["url"])
                raise SgdbNoImageFound()
            elif res.status == 401:
                raise SgdbAuthError()
            else:
                raise SgdbError()
    except Exception as e:
        if "401" in str(e):
            raise SgdbAuthError()
        elif "404" in str(e):
            raise SgdbNoImageFound()
        raise SgdbError(str(e))


def save_cover_from_url(game_id: str, url: str) -> bool:
    """Download, convert, resize, compress and save cover art to disk."""
    import PIL
    from PIL import Image, ImageSequence

    COVERS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        req = Request(url, headers={"User-Agent": "Cartridges/2.0"})
        with urlopen(req, timeout=10) as res:
            content = res.read()
    except Exception as e:
        logging.warning("Failed to download image from %s: %s", url, e)
        return False

    try:
        with Image.open(BytesIO(content)) as image:
            is_animated = getattr(image, "is_animated", False)
            if is_animated:
                frames = [
                    frame.resize((cover.WIDTH, cover.HEIGHT))
                    for frame in ImageSequence.Iterator(image)
                ]
                dest_path = COVERS_DIR / f"{game_id}.gif"
                (COVERS_DIR / f"{game_id}.tiff").unlink(missing_ok=True)
                frames[0].save(
                    dest_path,
                    save_all=True,
                    append_images=frames[1:],
                )
            else:
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGBA")
                dest_path = COVERS_DIR / f"{game_id}.tiff"
                (COVERS_DIR / f"{game_id}.gif").unlink(missing_ok=True)

                high_quality = SETTINGS.get_boolean("high-quality-images")
                resized = image.resize((cover.WIDTH, cover.HEIGHT))
                resized.save(
                    dest_path,
                    compression="tiff_adobe_deflate" if high_quality else "tiff_lzw",
                )
            return True
    except Exception as e:
        logging.warning("Failed to save cover image: %s", e)
        return False

