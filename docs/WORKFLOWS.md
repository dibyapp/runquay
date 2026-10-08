# Runquay workflow guide

Use this guide after [initial setup](GETTING_STARTED.md). Runquay is a local task queue around coding CLIs. It preserves goals, milestone results and file-based handoffs; it does not transfer full conversations between tools or certify generated code.

## Improve an existing repository

1. Commit or back up your current work before handing a repository to an agent. Runquay preserves existing files and instructions, but a build is authorized to change project files.
2. Choose **Tasks → Use an existing project → Connect folder**. Enter an existing absolute directory path and an optional display name. This registers the folder without moving or editing its files.
3. Find the connected card and choose **Add task**. This opens a goal for that repository, rather than creating a separate new project directory.
4. Describe the concrete change and acceptance checks. Include files or interfaces that must remain compatible. Choose the tool explicitly.
5. Add the goal, start the queue when ready, and inspect the results before committing or publishing.

Runquay avoids overlapping active tasks for the same workspace within its own supervisor. It cannot coordinate unrelated terminals, editors or other agent processes. Avoid making competing changes to the same files elsewhere while a milestone runs.

Expand **Use an existing project** in Tasks to see your saved folders. Folder paths and filenames are available under **Folder details**.

The running supervisor checkout cannot queue edits to itself. Use a separate development checkout when improving Runquay.

## Write goals that can be reviewed

A useful goal names the user-facing behavior, constraints, acceptance criteria and expected checks. For example:

```text
Add CSV export to the existing expense report.
The export must use the current date filter and include date, category,
description and amount. Preserve the existing report view and schema.
Test commas, quotes, Unicode and an empty result. Report the test command
and any remaining limitations. Do not deploy or change billing settings.
```

Avoid a vague goal such as "finish everything" for the first run. Break large projects into reviewable milestones. The cap is a stopping boundary, not a promise of completion. A blocked task may need your answer even when milestones remain.

## Ask the advisor for useful next work

1. Open **Ideas**.
2. Under **Project**, choose one repository or all connected projects. Choosing one keeps the analysis focused and filters saved suggestions to that project. Choose **All my projects** to see new-project ideas.
3. Expand **Choose the planning tool** to change providers. Only advisors with an enforced read-only mode are offered.
4. Enter a focus such as "find a small, testable improvement in the CSV importer".
5. Choose **Get ideas**. If the queue is paused, the advisor waits until it is started. Non-Codex planning needs one-invocation approval.
6. Read each suggestion's evidence, proposed goal, first milestone and effort. Choose **Review idea** to edit the goal and select the execution tool. A suggestion does not automatically become a build.

The advisor reads bounded project evidence and may use recent matching Codex chat previews. Relevant context is sent to the selected provider. Imported README files and chat previews can contain confidential information; choose repositories accordingly. Antigravity and custom tools currently have no verified read-only advisor.

Automatic suggestions run at the configured interval while the queue is enabled, behind higher-priority builds. Disable **Suggest new ideas automatically** if you want planning only on demand.

## Understand accounts, quotas and approvals

There is no profile-count cap. One worker uses a single selected provider at a time. Account eligibility and authentication remain provider-specific.

| Situation | Runquay behavior | Your next step |
| --- | --- | --- |
| Codex subscription quota available and paid balance verified zero | Eligible for a milestone | Review the goal, then start the queue. |
| Codex reaches the configured reserve | Stops and looks for another eligible Codex profile; otherwise waits | Wait for refresh or connect another permitted account you control. |
| Codex paid balance is positive or unknown | Blocks subscription-only work | Check the vendor account. Do not assume API-key or paid-credit use is allowed by this guard. |
| An earned reset is available | Presents a separate explicit decision | Approve one existing reset or keep waiting. Redemption cannot be undone. |
| Claude, Gemini, Antigravity or a custom CLI | Billing/quota is unverified; each invocation needs approval | Check the vendor account and possible charges before authorizing one run. |
| External provider errors | Does not automatically rotate accounts | Resolve the issue, disable the unavailable profile if needed and resume with another profile for that tool. |

Quota checks run before Codex milestones and during work. They are polling observations, not an atomic guarantee against spending if account settings change elsewhere. Runquay has no credit/reset purchase feature. Unlimited profiles are not unlimited AI usage or permission to bypass provider policies.

Unlinking a profile removes the Runquay connection and retains vendor credentials and historical files. Disabling a profile keeps it connected but removes it from eligible selection. Neither action revokes the vendor session; manage that through the vendor when needed.

## Pause, resume and recover

**Pause work** on Home stops scheduling and the active child work. Files already written remain on disk. **Pause task** affects that task; **Cancel task** removes it from active scheduling without rolling back its edits.

After a timeout, restart or interruption, inspect the repository and checkpoint first. The worker may have changed files before it stopped. Choose **Continue** (or **Add follow-up** for a finished task), explain what to do next, and set the milestone cap above the number already completed. Do not blindly repeat an operation that could have had external effects.

For a blocker, answer the actual question in the resume guidance. For a failed check, include the command, relevant sanitized error and intended behavior. Repeated failures are bounded; fix the cause instead of continually increasing limits. External-provider retries require new approvals.

The checkpoint file uses the legacy name `AUTOWORK_CHECKPOINT.md`. Later eligible accounts continue from project files and structured milestone results, not the previous account's complete chat transcript.

## Read task states

| State | Meaning |
| --- | --- |
| Waiting | Saved and waiting for a worker, eligible account or approval. A paused supervisor does not dispatch it. |
| Working | A milestone is active. Use activity output and inspect the actual files when appropriate. |
| Paused | Deliberately stopped. Review edits before resuming. |
| Needs you | A blocker, exhausted cap, restart or bounded failure needs review and guidance. Read the task's note. |
| Done | The agent reported the goal finished. Review code and rerun checks before accepting it. |
| Cancelled | No further milestones will be scheduled unless you explicitly resume it. Existing files remain. |

## Choose reasonable run settings

Work limits are collapsed initially so everyday settings are easier to scan.

- **Pause account at usage (%):** 50–90%. The reserve leaves room for in-flight work and other activity on the account.
- **Minutes per milestone:** 2–120. Use short milestones for initial integration checks and bounded changes; split large goals when useful.
- **Keep this device awake:** best effort. It cannot override shutdown, lid-close policy, updates or every OS power setting.
- **Automatic advisor:** useful for periodic proposals, but consumes provider allowance when it actually runs. Disable it for manual planning.
- **Hours between automatic advisor runs:** 1–72. Planning waits behind higher-priority builds.

Use **Save settings** to apply the form. Setup completion and settings changes do not implicitly approve a paid reset or an external invocation.

## Run across sign-ins and reboots

Start with foreground operation until a real task succeeds. For opt-in per-user startup, preview and then install the service from the Runquay checkout:

```sh
python runquay.py service preview
python runquay.py service install
```

Use `python3` on macOS/Linux if necessary. Windows uses Task Scheduler, macOS a LaunchAgent, and systemd Linux a user service. Startup depends on a usable user session and vendor credential store. The installer uses default data/port resolution; custom instances need a reviewed service definition.

Keep the computer powered, connected and signed in as required. A local installation cannot keep working while the device is shut down. Use only one supervisor for a data directory. Uninstall startup with `python runquay.py service uninstall`; runtime data is retained.

## Keep the work private

The dashboard is loopback-only. Coding prompts and relevant files still go to the chosen provider. Local programs running as your OS user share the trust boundary. Vendor hooks, extensions and wrappers have their own behavior.

Back up the data directory only after stopping the supervisor; it includes the database and private run state. Never upload that backup as a bug report. For reproducible reports, provide versions, sanitized steps and a small non-sensitive project. Review screenshots and logs manually before sharing. See [SECURITY.md](../SECURITY.md) and [OPERATIONS.md](OPERATIONS.md).
