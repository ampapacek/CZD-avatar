import hashlib
import re
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import main


class IndexPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main.app)

    def test_index_must_be_revalidated(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-cache")
        self.assertIn("text/html", response.headers["content-type"])

    def test_assets_carry_their_content_hash(self) -> None:
        html = self.client.get("/").text

        for name in ("styles.css", "avatar.bundle.js", "app.js"):
            expected = hashlib.sha256((main.static_dir / name).read_bytes()).hexdigest()[:12]
            self.assertIn(f"static/{name}?v={expected}", html)
        self.assertNotIn("?v=auto", html)

    def test_title_comes_from_settings(self) -> None:
        orig = main.settings
        main.settings = orig.model_copy(update={"app_title": "CZD-Demo <1>"})
        try:
            for name in ("index.html", "login.html"):
                html = main._render_page(name)
                self.assertIn("<title>CZD-Demo &lt;1&gt;", html)
                self.assertIn("<h1>CZD-Demo &lt;1&gt;</h1>", html)
                self.assertNotIn("{{APP_TITLE}}", html)
        finally:
            main.settings = orig

    def test_version_follows_file_contents(self) -> None:
        orig_dir = main.static_dir
        with tempfile.TemporaryDirectory() as tmp:
            main.static_dir = Path(tmp)
            try:
                (main.static_dir / "index.html").write_text(
                    '<script src="static/app.js?v=auto"></script>'
                    '<script src="static/missing.js?v=auto"></script>',
                    encoding="utf-8",
                )
                asset = main.static_dir / "app.js"
                asset.write_text("one", encoding="utf-8")
                first = re.search(r"app\.js\?v=(\w+)", main._render_page()).group(1)

                asset.write_text("two!", encoding="utf-8")
                second = re.search(r"app\.js\?v=(\w+)", main._render_page()).group(1)

                self.assertNotEqual(first, second)
                # A missing file keeps its reference untouched rather than failing the page.
                self.assertIn("static/missing.js?v=auto", main._render_page())
            finally:
                main.static_dir = orig_dir


if __name__ == "__main__":
    unittest.main()
