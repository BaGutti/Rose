"""League's Windows file and process names, pinned for tests.

The names come from config at import time and differ on macOS, where League is
an app bundle. Tests of the Windows layout start these patches so they run the
same on every platform.
"""

from unittest.mock import patch

import config
from injection.config import config_manager
from injection.game import game_detector, game_monitor
from injection.overlay import overlay_manager

WINDOWS_GAME_EXECUTABLES = ("League of Legends.exe", "League of Legends (TM) Client.exe")
WINDOWS_CLIENT_EXECUTABLE = "LeagueClient.exe"


def windows_game_layout():
    """The patches (not started) that pin the Windows names everywhere they are read."""
    return [
        patch.object(target, name, value)
        for target, name, value in (
            (config, "GAME_EXECUTABLE_NAMES", WINDOWS_GAME_EXECUTABLES),
            (config, "GAME_PROCESS_NAMES", WINDOWS_GAME_EXECUTABLES),
            (config, "CLIENT_EXECUTABLE_NAME", WINDOWS_CLIENT_EXECUTABLE),
            (game_detector, "MACOS", False),
            (game_detector, "GAME_EXECUTABLE_NAMES", WINDOWS_GAME_EXECUTABLES),
            (game_detector, "CLIENT_EXECUTABLE_NAME", WINDOWS_CLIENT_EXECUTABLE),
            (config_manager, "CLIENT_EXECUTABLE_NAME", WINDOWS_CLIENT_EXECUTABLE),
            (game_monitor, "_GAME_PROCESS_NAMES",
             frozenset(name.lower() for name in WINDOWS_GAME_EXECUTABLES)),
            (overlay_manager, "GAME_PROCESS_NAMES", WINDOWS_GAME_EXECUTABLES),
        )
    ]


def pin_windows_game_layout():
    """Start the Windows-name patches for the rest of the test module."""
    import unittest

    for patcher in windows_game_layout():
        patcher.start()
        unittest.addModuleCleanup(patcher.stop)
