"""Off Windows, Rose syncs its skins at startup without the Windows update dialog."""

import unittest
from unittest.mock import MagicMock, patch

from main.setup import skin_sync


class HeadlessSkinSyncTests(unittest.TestCase):
    def _sync(self, have_skins=True, have_previews=True, download=None):
        status = MagicMock()
        status.check_skins_downloaded.return_value = have_skins
        status.check_previews_downloaded.return_value = have_previews
        download = download or MagicMock(return_value=True)
        with patch.object(skin_sync, "AppStatus", return_value=status), \
                patch.object(skin_sync, "download_skins_on_startup", download):
            result = skin_sync.sync_skins_without_dialog()
        return result, status, download

    def test_a_missing_library_is_downloaded_in_full_and_marked_complete(self):
        result, status, download = self._sync(have_skins=False)

        self.assertTrue(result)
        self.assertTrue(download.call_args.kwargs["force_update"])
        status.update_status.assert_called_once_with(force=True)
        status.mark_download_process_complete.assert_called_once()

    def test_missing_previews_also_need_a_full_download(self):
        _, _, download = self._sync(have_previews=False)

        self.assertTrue(download.call_args.kwargs["force_update"])

    def test_an_existing_library_is_updated_incrementally(self):
        _, _, download = self._sync()

        self.assertFalse(download.call_args.kwargs["force_update"])

    def test_a_failed_download_is_not_marked_complete(self):
        result, status, _ = self._sync(download=MagicMock(return_value=False))

        self.assertFalse(result)
        status.mark_download_process_complete.assert_not_called()

    def test_a_download_that_raises_lets_rose_start_anyway(self):
        result, status, _ = self._sync(download=MagicMock(side_effect=OSError("offline")))

        self.assertFalse(result)
        status.mark_download_process_complete.assert_not_called()

    def test_progress_is_reported_to_the_log(self):
        def download(force_update, progress_callback):
            progress_callback(50, "Downloading skins")
            return True

        with self.assertLogs(skin_sync.log.name, level="INFO") as logs:
            self._sync(download=MagicMock(side_effect=download))

        self.assertTrue(any("Downloading skins" in line for line in logs.output))


if __name__ == '__main__':
    unittest.main()
