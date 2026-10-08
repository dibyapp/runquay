# Getting started with Runquay

Runquay runs your existing AI coding CLI on your computer. You describe a goal, choose the tool, and let a persistent local queue work through bounded milestones. This guide covers installation, all four onboarding steps, and your first task.

**Start here:** [Install](#1-install-the-prerequisites) · [Onboard](#3-complete-the-four-setup-steps) · [Build a project](#4-create-your-first-project) · [Review the result](#6-review-the-output)

For day-to-day use, read the [workflow guide](WORKFLOWS.md). For problems, use [troubleshooting](TROUBLESHOOTING.md). Check the [verification record](VERIFICATION.md) before assuming an OS or provider has been live-tested.

## 1. Install the prerequisites

You need **Python 3.11 or newer**, **Git**, and a supported vendor CLI with an account you are permitted to use. Runquay itself requires no Python packages. Individual AI tools may require Node, a sandbox runtime, authentication, or a paid subscription of their own.

### Windows

Install Python from [python.org](https://www.python.org/downloads/windows/) and Git from [git-scm.com](https://git-scm.com/downloads). Enable Python's PATH option when the installer offers it. Open a new PowerShell window after installation and check:

```powershell
py -3 --version
git --version
```

If the Python launcher is unavailable, try `python --version`. The version must be at least 3.11. If a command is missing, finish installation and reopen the terminal before continuing.

### macOS

Install a current Python from [python.org](https://www.python.org/downloads/macos/) and Git from [git-scm.com](https://git-scm.com/downloads). In Terminal, check:

```sh
python3 --version
git --version
```

Runquay's deterministic suite runs in macOS CI. That does not establish that vendor authentication, sandboxing or LaunchAgent installation has been manually exercised on your Mac.

### Ubuntu / Debian-based Linux

Install Python and Git through your distribution's package manager. On Ubuntu:

```sh
sudo apt update
sudo apt install python3 git
python3 --version
git --version
```

Confirm Python is 3.11+. Older distribution releases may need a newer supported Python installed through an appropriate source. Other Linux distributions use their own package names and service managers; the guide does not assume every distribution was tested.

### Install an AI coding tool

Use the tool's official installation instructions linked in [TOOLS.md](TOOLS.md). Authenticate through its official CLI or browser sign-in flow. Runquay does not install the vendor tool or take your password.

| Tool | What to expect in Runquay |
| --- | --- |
| Codex | Subscription authentication, verified quota and zero paid balance are required before a milestone starts. |
| Claude Code | CLI detection and adapter contracts are checked; each invocation needs approval because billing is unverified. |
| Gemini CLI | Contract-tested adapter; install and validate the vendor runtime and account on your machine. Each invocation needs approval. |
| Antigravity CLI | Requires the compatible headless `agy` tool. Editor installation alone is insufficient; isolated-home behavior and read-only planning are unverified. |
| Custom CLI | Supply a headless wrapper with the documented JSON result contract. The wrapper owns permissions and authentication. |

## 2. Download and start Runquay

Get the source ZIP from [GitHub Releases](https://github.com/dibyapp/runquay/releases/latest). Extract it into a folder you can write to. Keep the checkout at a stable location if you later enable startup services. Alternatively, clone the current source:

```sh
git clone https://github.com/dibyapp/runquay.git
cd runquay
```

In the extracted or cloned folder, start the launcher.

Windows:

```powershell
py -3 runquay.py start
```

macOS / Linux:

```sh
python3 runquay.py start
```

Windows can also use `start.cmd`; macOS/Linux can use `sh start.sh`. The launcher opens [127.0.0.1:8765](http://127.0.0.1:8765/). Keep the terminal running while using a foreground instance. Ctrl+C stops it; closing the browser tab alone does not stop the queue.

If Python is called `python` on your machine, substitute it in these commands. Do not expose the dashboard through a public proxy or tunnel. It is a local, single-user application.

## 3. Complete the four setup steps

The screenshots below are actual captures of Runquay running on Windows. Tool detection, account verification and project execution used the real backend. Views are cropped to keep unrelated private projects and personal paths out of the images. The workspace path shown is the actual dedicated folder used for the walkthrough. See [screenshot provenance](SCREENSHOTS.md).

### Step 1 — Tools

![Actual tool detection in Runquay onboarding](images/setup-tools.jpg)

Runquay lists supported CLIs and whether their executable is found. **Found** means detection succeeded; it is not proof of authentication, entitlement or live integration compatibility. Follow **Official setup documentation** if a tool is missing. Install the tool separately, then refresh or reopen the guide.

Choose a planning tool that supports a read-only advisor. Antigravity and custom tools currently have no verified read-only advisor, even though they can be execution adapters.

### Step 2 — Accounts

![An actual Codex login verified by Runquay](images/setup-accounts.jpg)

The first installation offers the current Codex login. A successful Codex check displays **Subscription verified**. Use **Sign-in guide** if authentication is required; run the displayed command in your terminal and finish the vendor flow there.

To connect another profile, choose **Connect another account**, select the tool and enter a local profile name. Check **Use this tool's current login** to reuse its existing login. Leave it unchecked for an isolated profile where supported. Then follow that profile's generated sign-in instructions and verify the connection.

![The actual account connection form before entering credentials](images/connect-account.jpg)

Do not paste passwords, API keys or auth files into profile names or command arguments. Adding profiles has no application count cap, but it does not increase a provider's allowance. Antigravity needs its current login or a custom wrapper with a verified isolation mechanism.

### Step 3 — Workspace

![Actual workspace selection](images/setup-workspace.jpg)

Choose an absolute folder path for **new** project workspaces. The walkthrough uses `C:\RunquayGuide\projects`; choose a suitable writable folder on your device. macOS/Linux examples could use a folder under your home directory. Each new task gets its own Git workspace inside the selected root.

**Connect a project folder** imports an existing directory into the library. The import reads filenames and a bounded README preview without editing project files. Saved Codex desktop roots are discovered automatically; other tools' projects can be connected manually. Existing tasks keep their original paths if you later change the new-project root.

### Step 4 — Review

![Actual setup review and billing acknowledgement](images/setup-review.jpg)

Read the workspace, provider and billing details, check the acknowledgement and choose **Finish setup**. On a new installation, the queue stays paused. Finishing setup does not authorize a paid reset or start a project. Reopening setup on an existing installation preserves the current start/pause state.

Open **Settings → Open setup guide** to revisit these steps.

## 4. Create your first project

Choose **Projects → New project**. Give the task a name, a concrete goal, an AI tool and a milestone cap. A smaller first task makes the initial integration easier to assess.

![Real project goal entered in the Runquay form](images/create-project.jpg)

The walkthrough used this goal:

> Build a small Python standard-library CLI in wordcount.py that reads a UTF-8 Markdown file and prints its word count. Add unittest tests for empty input, punctuation and Unicode. Include a short README with a runnable example. Run the tests and the CLI example; report the commands and results. No dependency installs, network calls, git commits or publishing. Complete within one milestone.

Choose **Codex**, set the milestone cap to **1**, and leave the model blank to use the account's available default. Choose **Add to queue**. This saves the task; it does not start a paused queue.

The priority field controls ordering: higher-priority work is selected ahead of lower-priority work. A milestone cap limits the number of turns, while **Minutes per milestone** limits a single turn. Neither is a guarantee that a goal can be completed within that budget.

## 5. Start and monitor

Choose **Start queue**. Runquay checks eligibility, selects an account for the task's chosen provider, and starts one milestone. Only one worker runs at a time. Other providers are not silently substituted.

![Actual Codex task running in the local dashboard](images/overview.jpg)

The overview shows supervisor status, waiting tasks, eligible accounts and completed projects. **Recent activity** provides run history and output. **Pause all** stops the queue and active child work. Use **Pause project** to stop only that task; review changed files before resuming an interrupted milestone.

If a task uses a tool with unverified billing, the approval inbox requests one invocation. Check the vendor account before approving. Every subsequent milestone or retry needs another approval. Codex earned resets are a separate explicit decision; waiting for natural refresh remains an option.

## 6. Review the output

![The actual completed word-counter task and its reported checks](images/completed-task.jpg)

Open the project's folder. Inspect the changed files, README, tests and `AUTOWORK_CHECKPOINT.md`. Read the reported commands and run relevant checks yourself. **Complete** means the agent reported completion; it is not an independent quality or security certification.

For this walkthrough, Codex wrote a real word-counter project and executed its checks. The documentation session also reran its tests independently. Exact observed results and screenshot context are recorded in [SCREENSHOTS.md](SCREENSHOTS.md).

For an existing repository, inspect `git diff` before committing. Launch completed applications separately: dev servers started by a worker stop with the milestone. Publishing, deployments and purchases remain separate actions.

## Next steps

- [Workflow guide](WORKFLOWS.md): existing repositories, AI suggestions, approvals, recovery and continuous use.
- [Troubleshooting](TROUBLESHOOTING.md): detection, quota, execution, state and startup issues.
- [Tool setup](TOOLS.md): adapter authentication, output contracts and verification boundaries.
- [Operations](OPERATIONS.md): data locations, backups, per-user startup and shutdown.
- [Security](../SECURITY.md): the local trust boundary and safe reporting.
