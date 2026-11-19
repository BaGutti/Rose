import sys
import unittest
from unittest import mock

from utils.system import admin_utils


@unittest.skipIf(sys.platform == "win32", "Windows asks for elevation through UAC")
class EnsureAdminRightsOffWindowsTests(unittest.TestCase):
    def test_starts_without_elevation_or_exit(self):
        with mock.patch.object(admin_utils, "request_admin_elevation") as elevate, \
                mock.patch.object(admin_utils, "show_admin_required_dialog") as dialog:
            admin_utils.ensure_admin_rights()

        elevate.assert_not_called()
        dialog.assert_not_called()


if __name__ == '__main__':
    unittest.main()
