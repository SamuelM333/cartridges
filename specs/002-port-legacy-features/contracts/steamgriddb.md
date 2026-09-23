# Contract: SteamGridDB Client Interface

This document specifies the interface contract between Cartridges and the external SteamGridDB v2 REST API, as well as the internal Python client interface implemented in `cartridges.utils.steamgriddb`.

## 1. External REST API Contract

### Authentication & Common Headers

All authenticated API requests must send:
```http
Authorization: Bearer {sgdb-key}
User-Agent: Cartridges/2.0
```

### Endpoints

#### 1. Autocomplete Search
* **Method**: `GET`
* **URL**: `https://www.steamgriddb.com/api/v2/search/autocomplete/{term}`
* **Path Parameters**:
  * `term` (string, URL-encoded): The game title to search for.
* **Response Status**:
  * `200 OK`: `{"success": true, "data": [{"id": 12345, "name": "..."}]}`
  * `401 Unauthorized`: API key missing or invalid.
  * `404 Not Found`: No game match found.

#### 2. Grid Cover Retrieval
* **Method**: `GET`
* **URL**: `https://www.steamgriddb.com/api/v2/grids/game/{id}?dimensions=600x900{&types=animated}`
* **Path Parameters**:
  * `id` (integer): The SteamGridDB game ID returned from autocomplete.
* **Query Parameters**:
  * `dimensions`: `600x900` (standard vertical cover ratio)
  * `types`: `animated` (optional, included when `sgdb-animated` is true)
* **Response Status**:
  * `200 OK`: `{"success": true, "data": [{"id": ..., "url": "https://...", "thumb": "https://...", ...}]}`
  * `401 Unauthorized`: API key missing or invalid.
  * `404 Not Found`: No cover artwork available for this game ID.

---

## 2. Python Client Module Contract (`cartridges.utils.steamgriddb`)

### Public Functions

#### `get_game_id(game_name: str) -> int`
* **Description**: Queries SteamGridDB autocomplete search and returns the first matching game ID.
* **Raises**:
  * `SgdbAuthError`: If API key is empty, whitespace, or rejected with HTTP 401.
  * `SgdbGameNotFoundError`: If no matching game is found on SteamGridDB.
  * `SgdbError`: For network errors, timeouts, or unexpected HTTP status codes.

#### `get_image_url(sgdb_id: int, animated: bool = False) -> str`
* **Description**: Fetches the top-rated 600x900 grid cover image URL for a given game ID.
* **Raises**:
  * `SgdbAuthError`: If API key is empty or rejected with HTTP 401.
  * `SgdbNoImageFoundError`: If no cover matches the criteria.
  * `SgdbError`: For network errors or unexpected status codes.

#### `get_grid_covers(sgdb_id: int) -> list[dict[str, Any]]`
* **Description**: Returns all available 600x900 grid covers for a game ID (used by `CoverPicker`).
* **Returns**: List of cover dictionaries containing `id`, `url`, `thumb`, `author`, `score`, and `style`. Returns `[]` on error.

#### `save_cover_from_url(game_id: str, url: str) -> bool`
* **Description**: Downloads cover art from `url`, resizes to Cartridges dimensions (`WIDTH=600`, `HEIGHT=900`), and saves to `COVERS_DIR / f"{game_id}.tiff"` (or `.gif` if animated).
* **Returns**: `True` if successfully saved; `False` on download or decode error.
