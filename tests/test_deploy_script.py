"""deploy/deploy.sh against a throwaway origin, with a fake restart and health check.

Health is read from a `status.txt` in the checked-out commit, so a commit whose
file says anything but `ok` plays the release that does not come up. The
systemd units and the sudoers rule can only be checked on the server.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "deploy.sh"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "needs git and bash")
class DeployScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.origin = self.tmp / "origin.git"
        self.dev = self.tmp / "dev"
        self.server = self.tmp / "server"
        self.restarts = self.tmp / "restarts"
        self.installs = self.tmp / "installs"

        self.git(self.tmp, "init", "--quiet", "--bare", "-b", "main", str(self.origin))
        self.git(self.tmp, "clone", "--quiet", str(self.origin), str(self.dev))
        self.git(self.dev, "checkout", "--quiet", "-b", "main")
        self.first = self.commit({"status.txt": "ok\n", "pyproject.toml": "deps = 1\n"})
        self.git(self.dev, "push", "--quiet", "origin", "main")
        self.git(self.tmp, "clone", "--quiet", str(self.origin), str(self.server))

    def git(self, cwd: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=cwd, env={**os.environ, **GIT_ENV},
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip()

    def commit(self, files: dict[str, str]) -> str:
        for name, content in files.items():
            (self.dev / name).write_text(content)
        self.git(self.dev, "add", "-A")
        self.git(self.dev, "commit", "--quiet", "-m", "change")
        return self.git(self.dev, "rev-parse", "HEAD")

    def push_production(self, sha: str, force: bool = False) -> None:
        self.git(self.dev, "push", "--quiet", *(["--force"] if force else []), "origin", f"{sha}:refs/heads/production")

    def deploy(self) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            **GIT_ENV,
            "REPO_DIR": str(self.server),
            "RESTART_CMD": f"echo restart >> {self.restarts}",
            "INSTALL_CMD": f"echo install >> {self.installs}",
            "HEALTH_CMD": "grep -qx ok status.txt",
            "HEALTH_TIMEOUT": "1",
            "HEALTH_INTERVAL": "0.2",
        }
        return subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)

    def head(self) -> str:
        return self.git(self.server, "rev-parse", "HEAD")

    def count(self, path: Path) -> int:
        return len(path.read_text().splitlines()) if path.exists() else 0

    def test_no_production_branch_does_nothing(self) -> None:
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.count(self.restarts), 0)

    def test_production_already_checked_out_does_nothing(self) -> None:
        self.push_production(self.first)
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.count(self.restarts), 0)

    def test_new_commit_is_checked_out_and_restarted(self) -> None:
        second = self.commit({"app.py": "v2\n"})
        self.push_production(second)
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.head(), second)
        self.assertEqual(self.git(self.server, "branch", "--show-current"), "production")
        self.assertEqual(self.count(self.restarts), 1)
        self.assertEqual(self.count(self.installs), 0)
        # The next run finds nothing new.
        self.deploy()
        self.assertEqual(self.count(self.restarts), 1)

    def test_dependency_change_reinstalls(self) -> None:
        second = self.commit({"pyproject.toml": "deps = 2\n"})
        self.push_production(second)
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.count(self.installs), 1)

    def test_unhealthy_commit_rolls_back_and_is_not_retried(self) -> None:
        broken = self.commit({"status.txt": "broken\n"})
        self.push_production(broken)
        result = self.deploy()
        self.assertEqual(result.returncode, 1)
        self.assertIn("rolled back", result.stdout)
        self.assertEqual(self.head(), self.first)
        self.assertEqual(self.count(self.restarts), 2)

        self.assertEqual(self.deploy().returncode, 0)
        self.assertEqual(self.count(self.restarts), 2)

        fixed = self.commit({"status.txt": "ok\n"})
        self.push_production(fixed)
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.head(), fixed)

    def test_force_pushing_an_older_commit_rolls_the_server_back(self) -> None:
        second = self.commit({"app.py": "v2\n"})
        self.push_production(second)
        self.deploy()
        self.push_production(self.first, force=True)
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.head(), self.first)

    def test_edits_on_the_server_block_the_deploy_and_are_kept(self) -> None:
        second = self.commit({"app.py": "v2\n"})
        self.push_production(second)
        (self.server / "status.txt").write_text("edited by hand\n")
        result = self.deploy()
        self.assertEqual(result.returncode, 1)
        self.assertIn("status.txt", result.stdout)
        self.assertEqual(self.head(), self.first)
        self.assertEqual((self.server / "status.txt").read_text(), "edited by hand\n")
        self.assertEqual(self.count(self.restarts), 0)
        # Reported once, not every minute.
        second_run = self.deploy()
        self.assertEqual(second_run.returncode, 0)
        self.assertEqual(second_run.stdout, "")

    def test_untracked_files_do_not_block_the_deploy(self) -> None:
        (self.server / "usage.csv").write_text("a,b\n")
        second = self.commit({"app.py": "v2\n"})
        self.push_production(second)
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.head(), second)
        self.assertTrue((self.server / "usage.csv").exists())


if __name__ == "__main__":
    unittest.main()
