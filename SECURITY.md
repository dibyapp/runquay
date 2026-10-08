# Security and privacy

Runquay is a single-user local tool. The dashboard binds to loopback, validates Host and Origin, uses a local session cookie and CSRF token, and serves only explicit assets. Do not publish its port. Programs running as your OS user can access its data and CLIs. It is not a public multi-user service.

Credentials belong to vendor CLIs and their credential stores. Runquay stores profile metadata, never a password field or credential export. Goals, files, README previews, and recent Codex chat previews may be sent to your selected AI service. Review provider data policies.

Runtime databases, accounts, logs, and projects are private. Credential-pattern log redaction is best effort; other personal information can remain. POSIX data directories use owner-only permissions; Windows relies on user directory ACLs. Choose a private data directory.

Native tool permissions determine effective access. Custom adapters add no sandbox. Imported projects, goals, and wrappers are trusted local work. Prompt instructions alone cannot enforce containment. Runquay has no telemetry; vendor CLIs may have their own telemetry, hooks, or network behavior.

Codex's quota guard is polling, not an atomic billing cutoff. Other tools have unverified billing and require per-invocation approval. No automatic purchases are implemented.

## Report vulnerabilities privately

Contact the repository owner privately; after publication, use private vulnerability reporting if enabled. Do not attach raw auth files, logs, account identifiers, or personal paths to public issues. Revoke leaked credentials through the provider; deleting a file does not remove Git history.

## Release safely

Run `python runquay.py release --check`, inspect the allowlisted ZIP, and review history. Seed a public repository only from reviewed source. Pattern scanning cannot detect every confidential value. Enable secret scanning and private vulnerability reporting when publishing. Never publish screenshots exposing private account or project details.

Documentation JPEGs are an explicit exception to raster-image exclusion: `release-manifest.json` pins visually reviewed image hashes under `docs/images`. Arbitrary images, changed image bytes and EXIF/XMP metadata are rejected. Pixel contents need human review; a checksum is not an image privacy detector. The published walkthrough captures the real application and a dedicated non-sensitive project, with private views outside the crop.
