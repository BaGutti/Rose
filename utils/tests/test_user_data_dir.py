import sys
import unittest
from pathlib import Path
from unittest import mock

from utils.core import paths


@unittest.skipUnless(sys.platform == "darwin", "macOS data folder convention")
class UserDataDirOnMacOSTests(unittest.TestCase):
    def setUp(self):
        self._saved = paths._cached_user_data_dir
        paths._cached_user_data_dir = None

    def tearDown(self):
        paths._cached_user_data_dir = self._saved

    def test_rose_keeps_its_data_in_application_support(self):
        with mock.patch.dict("os.environ", {"XDG_DATA_HOME": ""}):
            folder = paths.get_user_data_dir()

        self.assertEqual(folder, Path.home() / "Library" / "Application Support" / "Rose")


if __name__ == '__main__':
    unittest.main()
