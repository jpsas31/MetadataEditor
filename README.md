## MetadataEditor

Terminal UI (TUI) app to **browse a folder of MP3s**, **edit ID3 metadata**, **auto-fill from MusicBrainz/Spotify**, **manage album art**, **play tracks**, and **download audio from YouTube** (via `yt-dlp` + `ffmpeg`).

This project is built with:

- `urwid`: terminal UI
- `mutagen`: ID3 (title/artist/album + cover art)
- `musicbrainzngs` + `spotipy`: metadata lookup
- `miniaudio`: playback
- `yt-dlp`: YouTube download (audio → MP3)
- `climage` + `Pillow`: render album art as ASCII in the terminal

## What it does

- **Browse MP3s in a folder**: left panel shows the sorted `.mp3` files.
- **Edit metadata**: update **Title / Album / Artist**.
- **Cover art**:
  - Toggle cover art on the selected file (remove if it exists, otherwise fetch it).
  - Render cover art as ASCII in the “Music Player” view.
- **Auto-fill metadata**:
  - “Auto-fill Fields” (current track).
  - “Auto-fill for All Songs” (bulk; skips tracks that already have title/artist/album + cover).
  - Lookup order: **MusicBrainz first**, then **Spotify** fallback.
- **Playback**: play/pause/stop, next/previous, volume, loop, and a footer progress bar.
- **YouTube downloader**: paste a URL, hit Enter, download + convert to MP3 into the current folder.

## Requirements

- **Python**: `>= 3.13` (per `pyproject.toml`)
- **ffmpeg**: required for `yt-dlp` post-processing (`FFmpegExtractAudio` → MP3)
  - macOS (Homebrew): `brew install ffmpeg`
  - Linux (Debian/Ubuntu): `sudo apt-get install -y ffmpeg`

## Install

The repo includes `uv.lock`, so `uv` is the easiest/most reproducible option.

### Option A: `uv` (recommended)

```bash
uv sync
```

### Option B: install deps manually (quick-and-dirty)

```bash
python -m pip install -U urwid requests pillow spotipy miniaudio yt-dlp python-dotenv mutagen climage musicbrainzngs
```

## Spotify setup (optional but recommended)

Spotify is used as a fallback when MusicBrainz doesn’t return a good match.

- **Env vars**: the app reads `CLIENT_ID` and `CLIENT_SECRET` (loaded via `python-dotenv`)
- **How**:
  - Create an app in the Spotify Developer Dashboard: `https://developer.spotify.com/dashboard`
  - Put credentials in your environment or a local `.env` file in the project root:

```bash
export CLIENT_ID="..."
export CLIENT_SECRET="..."
```

If you skip this, auto-fill will still try MusicBrainz first; Spotify lookups may fail.

## Run

You must pass a directory containing `.mp3` files:

```bash
uv run python main.py /path/to/mp3/folder
```

Notes:

- If you’re not using `uv`, you can run it with plain Python (assuming deps are installed):

```bash
python main.py /path/to/mp3/folder
```

- The app `chdir`s into the provided directory (so YouTube downloads land there and file operations are relative).
- If you run without args, it raises a warning (“Provide a valid dir”).

## UI overview

### Views

- **Main View** (`1`):
  - **Left**: song list
  - **Right**: a two-section panel:
    - Metadata editor
    - YouTube downloader + status messages
- **Music Player** (`2`):
  - **Left**: same song list
  - **Right**: album art (ASCII) + track info (title/album/artist)

### Focusing panels

- **Left / Right arrows**: switch focus between the song list and the right panel.
- **Tab / Shift+Tab** (Main View right panel): switch focus between Metadata section and YouTube section.

## Editing metadata

In the Metadata editor panel:

- **Title / Album / Artist** fields:
  - Type your value
  - Press **Enter** to write the tag to the file
- **Set Cover**:
  - If the file has a cover → removes it
  - If the file has no cover → fetches cover art (if found) and embeds it
- **Auto-fill Fields**:
  - Fills title/artist/album (and cover art if available)
  - Does not overwrite an existing embedded cover art
- **Auto-fill for All Songs**:
  - Bulk operation with a progress bar
  - Skips tracks that already have title/artist/album + cover

## Download from YouTube

In the YouTube panel:

- Paste a YouTube URL into the input (`Escribe link:`)
- Press **Enter**
- The download runs in a background thread; status is displayed in the panel
- Output MP3 is written into the current music directory

If downloads fail, the most common cause is missing `ffmpeg`.

## Keyboard shortcuts (defaults)

Keybindings are **configurable** (see next section). These are the built-in defaults:

### Global

| Key   | Action                                                  |
| ----- | ------------------------------------------------------- |
| `esc` | Exit (if a popup is open, `esc` closes the popup first) |
| `F1`  | Help/status hint                                        |
| `1`   | Switch to Main View                                     |
| `2`   | Switch to Music Player                                  |
| `3`   | Reserved (no view by default)                           |

### Song list / playback

| Key              | Action                                 |
| ---------------- | -------------------------------------- |
| `up` / `down`    | Move selection (wrap-around)           |
| `left` / `right` | Focus list / focus right panel         |
| `a`              | Play selected track                    |
| `s`              | Toggle play/pause                      |
| `p`              | Stop                                   |
| `n` / `b`        | Next / previous                        |
| `+` / `=`        | Volume up                              |
| `-`              | Volume down                            |
| `0`              | Mute                                   |
| `m`              | Toggle mute                            |
| `l`              | Toggle loop                            |
| `delete`         | Delete selected file (no confirmation) |

## Keybind configuration

On startup the app **creates a default keybinds file if missing** and loads it once (restart the app to apply changes).

- **Path**: `$XDG_CONFIG_HOME/metadataEditor/keybinds.toml` (default: `~/.config/metadataEditor/keybinds.toml`)

### File format

The file is TOML with **context tables** (e.g. `[global]`, `[list]`) mapping **key → action_name**:

```toml
[global]
esc = "app_exit"
F1 = "show_help"
"1" = "view_switch_0"

[list]
up = "nav_up"
a = "playback_play"
```

Notes:

- **Keys** use `urwid` key names (`up`, `down`, `left`, `right`, `esc`, `delete`, `F1`, etc).
- **Unknown contexts** are ignored.
- **Unknown actions** are ignored (the key will do nothing).
- If the TOML is invalid/unreadable, the app falls back to built-in defaults.
- If you still have an old `keybinds.json` (from older versions), the app will **auto-migrate** it to `keybinds.toml` the first time it creates the TOML file.

### Contexts + fallback

Known contexts (today the UI primarily uses `global` + `list`):

- `global`
- `list`
- (reserved for future use): `metadata`, `youtube`, `popup`

Fallback behavior:

- When a key is pressed in a context (e.g. `list`), the app resolves it in that context first, then falls back to `global`.

### Supported action names

These are the action names currently registered by the app:

- **Global**
  - `app_exit`
  - `show_help`
  - `view_switch_0` (Main View)
  - `view_switch_1` (Music Player)
  - `view_switch_2` (reserved; no view by default)
- **List / playback**
  - `nav_up`, `nav_down`, `nav_left`, `nav_right`
  - `playback_toggle`, `playback_play`, `playback_stop`, `playback_next`, `playback_prev`
  - `volume_up`, `volume_down`, `volume_mute`, `volume_toggle_mute`
  - `loop_toggle`
  - `delete`

### Examples

Remap navigation to `j/k` (vim-ish) while keeping arrows:

```toml
[list]
up = "nav_up"
down = "nav_down"
j = "nav_down"
k = "nav_up"
```

Swap play/pause toggle to space:

```toml
[list]
" " = "playback_toggle"
s = "playback_toggle"
```

### Reset to defaults

Delete the file and re-run the app; it will recreate the default:

- `~/.config/metadataEditor/keybinds.toml`

### Keys not controlled here

Some keys are handled directly by the focused widget (not via the keybind config), for example:

- `enter` in metadata fields (writes the tag)
- `tab` / `shift tab` in the Main View right panel (switches between Metadata / YouTube sections)

## Caching

Album art rendered as ASCII in the Music Player view is cached (memory + disk):

- **Default cache dir**: `$XDG_CACHE_HOME/metadata_editor/album_art`
  - Default: `~/.cache/metadata_editor/album_art`

## Troubleshooting

### `yt-dlp` fails / “ffmpeg not found”

- Install `ffmpeg` and retry (see Requirements).

### Spotify auto-fill fails

- Ensure `CLIENT_ID` and `CLIENT_SECRET` are set (env or `.env`).

### No songs show up

- The app lists files containing `.mp3` in the provided directory.
- Run with the correct folder: `uv run python main.py /path/to/mp3/folder`.

### Debug logs

Album art/debug logging is written to:

- `/tmp/album_art_debug.log`

## Project structure (high level)

- `main.py`: entrypoint; initializes shared state and starts the `urwid` main loop
- `src/viewInfo.py`: scans the target folder and caches per-file metadata
- `src/tagModifier.py`: ID3 read/write + cover art embedding + auto-fill glue
- `src/spotifyInfo.py`: MusicBrainz + Spotify lookup logic
- `src/media.py`: playback engine (miniaudio)
- `src/youtube.py`: YouTube download via `yt-dlp`
- `src/urwid_components/`: UI widgets (views, footer, metadata editor, downloader panel, etc.)
