#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skin library sync at startup, without the Windows update dialog.

On Windows the launcher's update dialog syncs the skins
(launcher/sequences/skin_sync_sequence.py). That dialog is Win32, so on other
platforms Rose runs the same steps here and logs the progress instead: check
what is downloaded, download in full or only what changed, then mark the
download done.
"""

from typing import Optional

from state import AppStatus
from utils.core.logging import get_logger
from utils.download.skin_downloader import download_skins_on_startup

log = get_logger()

# Log the progress at most this often (percent)
PROGRESS_LOG_STEP = 10


def sync_skins_without_dialog() -> bool:
    """Download or update Rose's skin library. True when it is ready.

    A failure is logged and Rose starts anyway, as on Windows.
    """
    status = AppStatus()
    have_skins = status.check_skins_downloaded()
    have_previews = status.check_previews_downloaded()
    full = not (have_skins and have_previews)
    log.info(
        f"[SKINS] Syncing the skin library ({'full download' if full else 'checking for updates'})"
    )

    last_logged = [-PROGRESS_LOG_STEP]

    def progress(percent: int, message: Optional[str] = None) -> None:
        if message:
            log.info(f"[SKINS] {message}")
        if percent >= last_logged[0] + PROGRESS_LOG_STEP:
            last_logged[0] = percent
            log.info(f"[SKINS] {percent}%")

    try:
        success = download_skins_on_startup(force_update=full, progress_callback=progress)
    except Exception as e:  # noqa: BLE001 - a failed sync must never stop Rose
        log.error(f"[SKINS] Skin download failed: {e}")
        success = False

    status.update_status(force=True)
    if success:
        status.mark_download_process_complete()
        log.info("[SKINS] Skin library ready")
    else:
        log.warning("[SKINS] Skin download failed; continuing startup")
    return success
