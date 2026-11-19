"""League's macOS layout: an app bundle with the client and the game inside."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import config
from injection.config.config_manager import ConfigManager
from injection.game import game_detector
from injection.game.game_detector import GameDetector


def _executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"binary")
    return path


@unittest.skipUnless(sys.platform == "darwin", "macOS League layout")
class MacOSGamePathTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        # /Applications/League of Legends.app/Contents/LoL
        self.lol = Path(folder.name) / "League of Legends.app" / "Contents" / "LoL"
        self.client_exe = _executable(
            self.lol / "LeagueClient.app" / "Contents" / "MacOS" / "LeagueClient"
        )
        self.ux_exe = _executable(
            self.lol / "League of Legends.app" / "Contents" / "MacOS" / "LeagueClientUx"
        )
        _executable(self.lol / "Game" / "LeagueofLegends.app" / "Contents" / "MacOS" / "LeagueofLegends")
        self.config_manager = MagicMock(spec=ConfigManager)
        self.config_manager.load_league_path.return_value = None
        self.config_manager.load_client_path.return_value = None

    def _running(self, name, exe):
        process = MagicMock()
        process.info = {"pid": 1, "name": name, "exe": str(exe)}
        return patch.object(game_detector.psutil, "process_iter", return_value=[process])

    def test_the_game_process_is_named_without_an_extension(self):
        self.assertEqual(config.GAME_PROCESS_NAMES, ("LeagueofLegends",))

    def test_the_paths_are_found_from_the_running_client(self):
        with self._running("LeagueClient", self.client_exe):
            league, client = GameDetector(self.config_manager).detect_paths()

        self.assertEqual((league, client), (self.lol / "Game", self.lol))
        self.config_manager.save_paths.assert_called_once_with(str(self.lol / "Game"), str(self.lol))

    def test_the_paths_are_found_from_the_client_ux_too(self):
        with self._running("LeagueClientUx", self.ux_exe):
            league, client = GameDetector(self.config_manager).detect_paths()

        self.assertEqual((league, client), (self.lol / "Game", self.lol))

    def test_saved_macos_paths_are_accepted(self):
        self.config_manager.load_league_path.return_value = str(self.lol / "Game")
        self.config_manager.load_client_path.return_value = str(self.lol)

        with self._running("Finder", "/System/Library/CoreServices/Finder.app"):
            league, client = GameDetector(self.config_manager).detect_paths()

        self.assertEqual((league, client), (self.lol / "Game", self.lol))

    def test_the_client_folder_is_inferred_from_the_game_folder(self):
        inferred = ConfigManager.infer_client_path_from_league_path(str(self.lol / "Game"))

        self.assertEqual(inferred, str(self.lol))


if __name__ == '__main__':
    unittest.main()
