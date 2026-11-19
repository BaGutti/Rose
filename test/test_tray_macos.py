import argparse
import sys
import unittest
from unittest import mock

from main.setup import initialization


@unittest.skipUnless(sys.platform == "darwin", "macOS has no tray off the main thread")
class TrayOnMacOSTests(unittest.TestCase):
    def test_rose_starts_without_a_tray_icon(self):
        with mock.patch.object(initialization, "TrayManager") as tray_manager:
            result = initialization.initialize_tray_manager(argparse.Namespace())

        self.assertIsNone(result)
        tray_manager.assert_not_called()


if __name__ == '__main__':
    unittest.main()
