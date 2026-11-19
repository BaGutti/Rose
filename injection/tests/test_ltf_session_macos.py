"""Rose drives the macOS LTK Manager, whose bridge is built in (no launcher, no DLL)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from injection.overlay import ltf_session, ltk_data
from injection.overlay.process_manager import LTK_MANAGER_PROCESSES
from injection.tests.test_ltf_session import FakeBridge, LtfSessionTestCase
from injection.tools import tools_manager
from injection.tools.tools_manager import ToolsManager


class MacOSManagerStartTests(LtfSessionTestCase):
    def setUp(self):
        super().setUp()
        native = patch.object(ltf_session, "NATIVE_BRIDGE", True)
        native.start()
        self.addCleanup(native.stop)
        # Rose ships no LTF runtime on macOS
        (self.tools / "ltk_launcher.exe").unlink()
        (self.tools / "LeagueToolFlop.dll").unlink()

    def test_the_manager_is_started_directly_and_its_bridge_awaited(self):
        mod = self.make_mod()
        started = MagicMock(pid=4242)
        with patch.object(ltf_session, "find_bridge", return_value=None), \
                patch.object(ltf_session.subprocess, "Popen", return_value=started) as popen, \
                patch.object(ltf_session.subprocess, "run") as launcher:
            result = self.overlay.mk_run_overlay([mod], stop_callback=lambda: True)

        self.assertEqual(result, 0)
        launcher.assert_not_called()
        self.assertEqual(popen.call_args.args[0], [str(self.root / "ltk-manager.exe")])
        self.assertIn(("wait_for_bridge", 4242), FakeBridge.created[0].calls)
        self.assertEqual(self.state()["manager"]["pid"], 4242)
        self.assertNotIn("LTF_MISSING", self.reported_codes())

    def test_the_manager_stays_open_after_the_game(self):
        # Its patcher host keeps root between games: closing it would ask for
        # the administrator password again at the next one
        mod = self.make_mod()
        with patch.object(ltf_session, "find_bridge", return_value=None), \
                patch.object(ltf_session.subprocess, "Popen", return_value=MagicMock(pid=4242)):
            self.overlay.mk_run_overlay([mod], stop_callback=lambda: True)

        self.assertNotIn("kill", self.bridge.command_names())
        self.assertNotIn(4242, self.terminated)
        self.assertIn("stop_patcher", self.bridge.command_names())

    def test_the_next_game_reuses_the_open_manager(self):
        mod = self.make_mod()
        with patch.object(ltf_session, "find_bridge", return_value=None), \
                patch.object(ltf_session.subprocess, "Popen", return_value=MagicMock(pid=4242)):
            self.overlay.mk_run_overlay([mod], stop_callback=lambda: True)

        mod = self.make_mod()
        with patch.object(ltf_session, "find_bridge", return_value=(46321, {"pid": 4242})), \
                patch.object(ltf_session.subprocess, "Popen") as popen:
            result = self.overlay.mk_run_overlay([mod], stop_callback=lambda: True)

        self.assertEqual(result, 0)
        popen.assert_not_called()
        self.assertNotIn("kill", self.bridge.command_names())

    def test_a_manager_that_never_serves_its_bridge_is_stopped(self):
        mod = self.make_mod()

        def never(cls, timeout=30.0, expected_pid=None, cancelled=None):
            raise ltf_session.BridgeUnavailable("no bridge")

        with patch.object(ltf_session, "find_bridge", return_value=None), \
                patch.object(ltf_session.subprocess, "Popen", return_value=MagicMock(pid=4242)), \
                patch.object(FakeBridge, "wait_for_bridge", classmethod(never)):
            self.overlay.mk_run_overlay([mod], stop_callback=lambda: True)

        self.assertIn(4242, self.terminated)

    def test_a_manager_that_cannot_start_is_reported(self):
        mod = self.make_mod()
        with patch.object(ltf_session, "find_bridge", return_value=None), \
                patch.object(ltf_session.subprocess, "Popen", side_effect=OSError("denied")):
            self.overlay.mk_run_overlay([mod], stop_callback=lambda: True)

        self.assertIn("start", self.reported_causes())
        self.assertIn("could not start LTK Manager", self.host.last_failure_reason)


class MacOSLocationTests(unittest.TestCase):
    def setUp(self):
        for module in (tools_manager, ltk_data):
            macos = patch.object(module, "MACOS", True)
            macos.start()
            self.addCleanup(macos.stop)

    def test_the_runtime_check_needs_no_launcher_files(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertTrue(ToolsManager(Path(empty)).check_tools_available())

    def test_the_manager_is_found_inside_its_app_bundle(self):
        with tempfile.TemporaryDirectory() as apps:
            macos_dir = Path(apps) / "LTK Manager Unofficial.app" / "Contents" / "MacOS"
            macos_dir.mkdir(parents=True)
            (macos_dir / "ltk-manager").write_bytes(b"binary")
            with patch.object(tools_manager, "ltk_manager_install_dirs", return_value=[macos_dir]), \
                    patch.object(ToolsManager, "_configured_ltk_manager", return_value=None), \
                    patch.object(ToolsManager, "_running_ltk_manager", return_value=None):
                found = ToolsManager(Path(apps)).detect_ltk_manager()

        self.assertEqual(found, macos_dir / "ltk-manager")

    def test_the_install_dirs_are_the_app_bundles(self):
        dirs = tools_manager.ltk_manager_install_dirs()

        self.assertIn(
            Path("/Applications/LTK Manager Unofficial.app/Contents/MacOS"), dirs
        )

    def test_the_manager_process_is_recognised_by_its_macos_name(self):
        self.assertIn("ltk-manager", LTK_MANAGER_PROCESSES)

    def test_ltk_data_and_logs_are_in_the_macos_folders(self):
        support = Path.home() / "Library" / "Application Support"

        self.assertEqual(
            ltk_data.ltk_data_candidates()[0], support / "io.github.bagutti.ltk-manager-macos"
        )
        self.assertIn(support / "dev.leaguetoolkit.manager", ltk_data.ltk_data_candidates())
        self.assertEqual(
            ltk_data.ltk_log_candidates()[0],
            Path.home() / "Library" / "Logs" / "io.github.bagutti.ltk-manager-macos",
        )



class MacOSLtkSettingsTests(unittest.TestCase):
    """macOS keeps LTK Manager's logs apart from its data (~/Library/Logs)."""

    def test_ltk_managers_settings_are_read_from_its_data_folder(self):
        import json
        with tempfile.TemporaryDirectory() as root:
            data = Path(root) / "Application Support" / "ltk"
            logs = Path(root) / "Logs" / "ltk"
            data.mkdir(parents=True)
            logs.mkdir(parents=True)
            (data / "settings.json").write_text(
                json.dumps({"builtinMods": {"baseSkins": "allChampions"}}), encoding="utf-8"
            )
            report = MagicMock()
            with patch.object(ltk_data, "MACOS", True), \
                    patch.object(ltk_data, "ltk_data_dir", return_value=data), \
                    patch.object(ltk_data.LtkLogTail, "log_dir", staticmethod(lambda: logs)), \
                    patch.object(ltf_session, "report_issue", report):
                ltf_session.LtfHost._check_ltk_builtins()

        self.assertEqual(report.call_args.args[0], "LTK_HEAVY_BUILTINS")


if __name__ == '__main__':
    unittest.main()
