import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from release import ROOT, audit, source_files, has_credential, public_images


class ReleaseTests(unittest.TestCase):
    def test_manifest_excludes_runtime_and_private_assets(self):
        files = source_files()
        names = [p.relative_to(ROOT).as_posix() for p in files]
        self.assertIn("LICENSE", names)
        self.assertIn("web/setup.js", names)
        self.assertIn(".github/workflows/ci.yml", names)
        self.assertFalse(any(p.startswith(("data/", "projects/", ".research/", "dist/")) for p in names))
        self.assertFalse(any("__pycache__" in p or p.endswith((".sqlite3", ".jsonl", ".png")) for p in names))
        self.assertEqual({p for p in names if p.endswith(".jpg")}, set(public_images()))

    def test_only_reviewed_image_bytes_can_enter_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            images = root / "docs/images"
            images.mkdir(parents=True)
            public = images / "reviewed.jpg"
            reviewed = b"\xff\xd8\xff\xe0reviewed-image-fixture\xff\xd9"
            public.write_bytes(reviewed)
            private = images / "private-unreviewed.jpg"
            private.write_bytes(b"unreviewed screenshot must not ship")
            manifest = {"files": [], "directories": ["docs"], "public_images": {"docs/images/reviewed.jpg": [hashlib.sha256(reviewed).hexdigest()]}}
            (root / "release-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(source_files(root), [public])
            self.assertEqual(audit(source_files(root), root), [])
            public.write_bytes(reviewed + b"changed since review")
            self.assertTrue(audit(source_files(root), root))
            self.assertTrue(audit([private], root))

    def test_even_pinned_images_with_private_metadata_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            file = root / "docs/images/photo.jpg"
            file.parent.mkdir(parents=True)
            raw = b"\xff\xd8\xff\xe1Exif\x00\x00private metadata\xff\xd9"
            file.write_bytes(raw)
            (root / "release-manifest.json").write_text(json.dumps({"public_images": {"docs/images/photo.jpg": [hashlib.sha256(raw).hexdigest()]}}), encoding="utf-8")
            self.assertIn("EXIF", audit([file], root)[0])

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
