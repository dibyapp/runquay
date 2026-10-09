# AI coding CLI setup: Codex, Claude Code, Gemini, and Antigravity

Install vendor tools from their official sources, authenticate there, then connect profiles in Runquay. The [automatic setup assistant](SETUP.md) can install missing Codex, Claude Code and Gemini CLI helpers from fixed official packages. Installation does not sign you into an AI service. It makes no guarantees about vendor account entitlement or plan availability.

| Tool | Official documentation | Expected CLI |
| --- | --- | --- |
| Codex | [Non-interactive execution](https://learn.chatgpt.com/docs/non-interactive-mode), [app-server](https://learn.chatgpt.com/docs/app-server) | `codex` |
| Claude Code | [CLI reference](https://code.claude.com/docs/en/cli-reference), [configuration](https://code.claude.com/docs/en/settings) | `claude` |
| Gemini CLI | [Headless mode](https://geminicli.com/docs/cli/headless/), [configuration](https://geminicli.com/docs/reference/configuration/) | `gemini` |
| Antigravity CLI | [Headless mode](https://antigravity.google/docs/cli/headless/), [CLI reference](https://antigravity.google/docs/cli/reference/) | `agy` |

## Codex

The adapter uses official app-server methods for account, model, subscription quota, recent chats, and earned reset credits. Workers force ChatGPT authentication and the OpenAI provider, ignore user configuration, disable optional plugins/apps/hooks/browser and subagent tools, and use the native workspace sandbox. Managed policies can impose stricter limits. The locally tested build is `0.162.0-alpha.2`; other versions may reject flags or lack quota/reset methods and fail closed.

Additional profiles have separate `CODEX_HOME` directories and request the vendor keyring credential store. Keyring availability varies by OS/session; complete sign-in in a usable desktop/session and verify quota. Runquay never copies the current login. The desktop's bundled Windows CLI is preferred when available; otherwise PATH is used. You can explicitly select a binary path.

Separate Codex profiles offer **Sign in with Codex**, which launches the installed CLI's [official ChatGPT browser OAuth](https://learn.chatgpt.com/docs/cli/reference). Credentials remain under the vendor's [authentication and keyring handling](https://learn.chatgpt.com/docs/auth); Runquay does not collect passwords, proxy OAuth callbacks, or publish sign-in URLs. One browser login runs at a time. Finish in the browser, then return to Runquay for the automatic connection check. A desktop browser, an available local callback port and a usable OS keyring are needed; browser launch/callback or keyring failures may require the collapsed terminal fallback. Attempts time out after five minutes and can be cancelled. The current shared Codex app login is reused rather than replaced. Other tools retain their terminal flow.

## Claude Code

Local flag inspection used version `2.1.251`. Print mode returns a structured JSON envelope. Read-only planning exposes only Read/Glob/Grep. Builds use `dontAsk`, Edit/Write and a small allowlist of test/status commands; other approval-required tools are denied. `--safe-mode` suppresses customizations, `--strict-mcp-config` with an empty config removes MCP servers, and user/project setting sources are omitted. No bypass mode is enabled.

Native permissions are not a guarantee of total filesystem/network containment. New dependencies or broader shell access may block a task. Sign in via the profile's generated `CLAUDE_CONFIG_DIR` command. Confirm that your installed version and OS keep authentication isolated as expected before adding multiple accounts; some vendor credential stores have their own global behavior. Model execution has not been live-tested for this release.

## Gemini CLI

`GEMINI_CLI_HOME` points at a profile root; the CLI creates its `.gemini` state inside it. Headless JSON returns a response string, which must contain Runquay's checkpoint object. Plan mode is used for analysis, `auto_edit` for builds, and the vendor sandbox is requested. A sandbox runtime may be required, depending on OS and vendor configuration. Missing runtime, trust decisions, tool approval, or invalid output stop/retry the milestone; no yolo mode is used. Project policies and extensions remain vendor-controlled. No live account validation was available here.

## Antigravity

The execution adapter targets **Antigravity CLI (`agy`)**. Separately, the read-only history adapter can display available local desktop, IDE and CLI transcripts; this does not enable editor automation or decrypt older conversation files. [History sources and limitations](TASK_HISTORY.md). Print mode uses cached vendor credentials and JSON/schema output; terminal sandboxing is requested. Permission-required commands can be soft-denied in headless mode. Configure narrow vendor permission rules yourself, never a blanket permission bypass.

No isolated-home override has been established from the inspected official interface. Runquay therefore accepts only the current login for the built-in adapter. Multiple isolated Antigravity accounts require a custom wrapper with a verified isolation mechanism. The advisor is disabled because a reliable read-only policy has not been established. No live account validation was available here.

## Saved conversation history

**Tasks → Existing AI tasks** detects native local Codex, Claude Code, Gemini CLI and available Antigravity histories. History detection does not require another connection or provider invocation. Other tools can import the documented metadata JSON format; execution through a custom wrapper remains a separate setup. [History guide](TASK_HISTORY.md).

## Any compatible headless tool

Create a **Custom CLI** profile with an argument array, not a shell string:

```json
["your-wrapper", "--schema", "{schema}", "--workspace", "{workspace}"]
```

Runquay resolves the executable and launches with `shell=False`. Prompts go through stdin, avoiding process-list exposure and argument-length limits. Optional placeholders are `{schema}` and `{workspace}`. The wrapper must authenticate through its vendor, enforce its own profile isolation and permissions, and emit **only one JSON checkpoint object on stdout**. Diagnostics go to stderr. Example response:

```json
{"status":"continue","summary":"Implemented the first milestone","tests":"Describe actual checks","next_step":"Next useful milestone","question":""}
```

The custom wrapper receives `AUTOWORK_PROFILE_HOME` with its private profile directory. Use it explicitly for vendor state; Runquay cannot enforce that a wrapper respects it.

Use `complete` only when the stated goal passes acceptance checks; use `blocked` with an exact question for missing permission or information. Runquay rejects malformed output. Each invocation requires approval; adding a command does not establish subscription-only billing. Never put keys, tokens, passwords, or sensitive arguments in the stored command array. [Synthetic adapter example](../examples/custom_cli.py) makes no AI requests and demonstrates the wire contract.

Windows npm `.cmd` shims are resolved to Node + their script where possible, avoiding shell interpolation. Unrecognized wrappers are rejected; select a native executable or a trusted wrapper instead.
