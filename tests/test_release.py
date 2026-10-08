import json
from pathlib import Path
import tempfile
import unittest

from release import ROOT, audit, source_files, has_credential


class ReleaseTests(unittest.TestCase):
    def test_manifest_excludes_runtime_and_private_assets(self):
        files = source_files()
        names = [p.relative_to(ROOT).as_posix() for p in files]
        self.assertIn("LICENSE", names)
        self.assertIn("web/setup.js", names)
        self.assertIn(".github/workflows/ci.yml", names)
        self.assertFalse(any(p.startswith(("data/", "projects/", ".research/", "dist/")) for p in names))
        self.assertFalse(any("__pycache__" in p or p.endswith((".sqlite3", ".jsonl", ".jpg", ".png")) for p in names))

    def test_current_source_has_no_detected_private_content(self):
        self.assertEqual(audit(source_files()), [])

    def test_audit_detects_credential_email_and_home_without_echoing_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); file = root/"fixture.md"
            secret = "sk-" + "x"*35
            email = "private-person" + "@" + "private.invalid"
            file.write_text(secret + "\n" + email + "\n" + str(Path.home()), encoding="utf-8")
            findings = audit([file], root)
            self.assertEqual(len(findings), 3)
            self.assertNotIn(secret, str(findings))
            self.assertNotIn(email, str(findings))

    def test_allowlist_rejects_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"release-manifest.json").write_text(json.dumps({"files":["missing.py"],"directories":[]}), encoding="utf-8")
            with self.assertRaises(ValueError): source_files(root)

    def test_historical_fixture_literal_is_not_a_real_credential(self):
        self.assertFalse(has_credential('API_KEY: "test-key'))
        self.assertTrue(has_credential('API_KEY: "' + 'real-credential-value'))


if __name__ == "__main__": unittest.main()
