# Automatic setup for Windows, macOS and Linux

Download and extract [the latest source ZIP](https://github.com/dibyapp/runquay/releases/latest). Keep the folder intact. Runquay detects your computer and offers a setup plan for the AI tool you choose.

| Computer | First launch | What happens if essentials are missing |
| --- | --- | --- |
| Windows | Double-click **setup.cmd** | WinGet installs missing Python 3.13 and Git. Complete any vendor agreement or OS permission prompts in its window. |
| macOS | Open **setup.command** | Homebrew installs missing Python 3.13 and Git. If Homebrew is missing, its official installer starts in Terminal; review and finish its prompts. |
| Ubuntu / Debian | Run **sh setup.sh** in the extracted folder | apt installs missing Python and Git. OS administrator prompts stay in Terminal. Python must be 3.11 or newer. |
| Fedora / Arch / openSUSE | Run **sh setup.sh** | The matching dnf, pacman or zypper path installs missing essentials. |

Existing compatible Python and Git are reused. No full-system upgrade runs. Keep the launcher window open during foreground use. **start.cmd**, **start.command**, **sh start.sh**, and **python runquay.py start** remain available for an already prepared computer. The first-launch files do not sign in, start a model request or buy anything.

## In the dashboard

1. **Tool:** Runquay shows the detected OS and recommends a verified account or installed tool. Choose another AI tool if you prefer. If something is missing, read the listed software and choose **Install missing tools**. Wait for **Tools are ready**, then choose **Next**.
2. **Account:** names and profile settings are filled automatically. A verified current Codex login is reused. If there is no Codex connection, a separate profile opens **Sign in with Codex**. Finish on OpenAI's website, then return. Claude and Gemini keep their official terminal sign-in instructions; installation alone does not establish authentication or billing.
3. **Folder:** keep the suggested folder or choose your own. Existing Codex project roots are discovered; other folders can be connected manually.
4. **Ready:** review the workspace and billing rules, acknowledge them and finish setup. Work starts only when you choose **Start work**. Installing a tool does not purchase a subscription or approve an AI invocation.

Installation supports fixed official npm packages for Codex, Claude Code and Gemini CLI. Missing Node.js is installed privately from the official Node.js 22 download for Windows/macOS/Linux on x64 or ARM64. The downloaded archive must match the official HTTPS checksum listing before extraction. Archive paths are bounded; special files and links are not extracted. Node.js 22+ already on the computer is reused. Existing AI helpers are left in place.

Vendor packages use a separate Runquay tools prefix with the official npm registry. Runquay discovers these tools without editing your shell startup files or global npm prefix. Vendor package installation can run that package's installation scripts, just as a normal official package-manager installation does. This is software installation on your computer, not a sandboxed preview. Work and sign-in must be paused while installing.

## Permissions or installation errors

The dashboard never accepts administrator passwords or silently accepts vendor agreements. If an OS/package manager needs interaction, expand **Manual setup or troubleshooting**, copy its instruction into PowerShell or Terminal, finish the prompts there, then choose **Check again**. The instruction is generated for the running Python executable and extracted app folder, so it also works when they are not on PATH.

The CLI equivalent is:

```sh
python runquay.py setup --provider codex
python runquay.py setup --provider codex --install
```

The first command reports a plan without installing. The second installs its missing tools and keeps permission prompts and detailed package-manager errors in the terminal. Replace `codex` with `claude` or `gemini`. Use `python3` on Unix if needed. Antigravity and custom wrappers need their official/manual installation; Runquay does not guess an installer for a GUI-only product.

Windows needs [WinGet/App Installer](https://learn.microsoft.com/en-us/windows/package-manager/winget/) for missing Python/Git. The default **setup.cmd** uses native batch commands and does not change PowerShell execution policy. The optional **Setup-Runquay.ps1** helper obeys that policy; restricted organizations can use the batch entry point or their approved installation process. macOS may require Apple Command Line Tools and Homebrew's own setup prompts. Older Linux releases may ship Python below 3.11 and require a newer supported Python installation. Non-systemd Linux can run in the foreground; optional startup uses a suitable service manager. Unsupported CPUs, package managers, locked-down computers and unavailable vendor packages get a manual guide.

Runquay startup-on-login remains optional; see [the startup guide](GETTING_STARTED.md). There is no unattended installation of system services during onboarding.

## Official sources and verification

- [Python downloads](https://www.python.org/downloads/) and [Git downloads](https://git-scm.com/downloads)
- [Homebrew installation](https://docs.brew.sh/Installation) and [WinGet installation commands](https://learn.microsoft.com/en-us/windows/package-manager/winget/install)
- [Node.js release downloads](https://nodejs.org/en/download)
- [Codex CLI](https://learn.chatgpt.com/docs/cli), [Claude Code setup](https://code.claude.com/docs/en/setup), [Gemini CLI installation](https://geminicli.com/docs/get-started/installation/)

A real Windows dashboard test installed the private Node.js runtime and Gemini CLI and checked `gemini --version` successfully. No Gemini sign-in or model request was executed. OS package recipes, checksums, archive boundaries, fixed package selection, concurrency and local-session/CSRF requirements have deterministic tests. Windows and Ubuntu first-launch detection were checked locally. Native macOS installation and Linux privileged installs remain separate integration checks; CI alone does not prove those interactions. See [the verification record](VERIFICATION.md) and [actual screenshot](SCREENSHOTS.md).
