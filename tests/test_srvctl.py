from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRVCTL_PATH = ROOT / "tools/srvctl"


def load_srvctl():
    loader = SourceFileLoader(
        "ai_project_srvctl",
        str(SRVCTL_PATH),
    )
    spec = spec_from_loader(
        loader.name,
        loader,
    )

    if spec is None:
        raise RuntimeError(
            "unable to create srvctl module spec"
        )

    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


srvctl = load_srvctl()


class SrvctlTests(unittest.TestCase):
    def test_json_flag_is_accepted_before_command(self):
        args = srvctl.build_parser().parse_args(
            [
                "--json",
                "autopilot",
            ]
        )

        self.assertTrue(args.json)
        self.assertEqual(
            args.command,
            "autopilot",
        )

    def test_json_flag_is_accepted_after_command(self):
        args = srvctl.build_parser().parse_args(
            [
                "autopilot",
                "--json",
            ]
        )

        self.assertTrue(args.json)
        self.assertEqual(
            args.command,
            "autopilot",
        )

    def test_api_venv_is_preferred_for_pytest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            python = (
                root
                / "apps/api/.venv/bin/python"
            )
            python.parent.mkdir(
                parents=True,
            )
            python.touch()

            with patch.object(
                srvctl,
                "ROOT",
                root,
            ):
                command = (
                    srvctl.api_pytest_command()
                )

        self.assertEqual(
            command,
            (
                str(python),
                "-m",
                "pytest",
            ),
        )

    def test_api_pytest_has_safe_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(
                srvctl,
                "ROOT",
                Path(tmp),
            ):
                command = (
                    srvctl.api_pytest_command()
                )

        self.assertEqual(
            command,
            (
                "python3",
                "-m",
                "pytest",
            ),
        )

    def test_missing_executable_returns_rc_127(self):
        error = FileNotFoundError(
            2,
            "No such file or directory",
            "missing-command",
        )

        with patch.object(
            srvctl.subprocess,
            "run",
            side_effect=error,
        ):
            result = srvctl.run(
                "missing-command"
            )

        self.assertEqual(
            result.returncode,
            127,
        )
        self.assertIn(
            "FileNotFoundError",
            result.stderr,
        )


if __name__ == "__main__":
    unittest.main()

