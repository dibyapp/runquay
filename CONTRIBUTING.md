# Contributing

Use Python 3.11+ and Git. No Python dependencies are required. Run `python runquay.py start` and `python -m unittest discover -s tests -v`. Check JavaScript with `node --check web/app.js` and `node --check web/setup.js`.

Explain the concrete problem, resulting behavior, validation, and limitations. Never commit runtime data, credentials, real account identifiers, or personal project screenshots. Run the release audit before opening a pull request.

Adapters must document official CLI sources, tested versions, argv construction, authentication scope, account isolation, permission boundaries, output parsing, quota behavior, and supported OSes. Never silently inherit paid credentials, bypass permissions, or label a contract-only integration as live verified. Unknown billing needs per-invocation approval. Test malformed output, provider errors, approval consumption, pause, and cleanup with a synthetic CLI.

OS changes need paths-with-spaces checks, process containment, service definitions, and shutdown validation. UI changes must preserve keyboard access, labels, narrow layouts, and onboarding. Keep implementation jargon out of normal task flows.
