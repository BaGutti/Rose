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



@unittest.skipIf(sys.platform == "win32", "Windows registers auto-start with schtasks")
class AutostartOffWindowsTests(unittest.TestCase):
    def test_auto_start_reads_as_off_without_running_schtasks(self):
        with mock.patch.object(admin_utils.subprocess, "run") as run:
            self.assertFalse(admin_utils.is_registered_for_autostart())

        run.assert_not_called()

    def test_registering_auto_start_says_it_is_windows_only(self):
        with mock.patch.object(admin_utils.subprocess, "run") as run:
            for change in (admin_utils.register_autostart, admin_utils.unregister_autostart):
                ok, message = change()
                self.assertFalse(ok)
                self.assertIn("only available on Windows", message)

        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
