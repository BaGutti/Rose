import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lcu.core import lockfile


class LockfileCandidateTests(unittest.TestCase):
    def _candidate_for_process(self, process_name):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "lockfile"
            path.write_text("LeagueClient:4242:53210:secret:https", encoding="utf-8")
            process = mock.Mock()
            process.name.return_value = process_name
            with mock.patch.object(lockfile.psutil, "Process", return_value=process):
                return lockfile._is_lockfile_candidate(path)

    def test_a_windows_client_lockfile_is_kept(self):
        self.assertTrue(self._candidate_for_process("LeagueClient.exe"))

    def test_a_macos_client_lockfile_is_kept(self):
        self.assertTrue(self._candidate_for_process("LeagueClient"))

    def test_a_macos_client_ux_lockfile_is_kept(self):
        self.assertTrue(self._candidate_for_process("LeagueClientUx"))

    def test_a_lockfile_left_by_another_process_is_dropped(self):
        self.assertFalse(self._candidate_for_process("Finder"))


if __name__ == '__main__':
    unittest.main()
