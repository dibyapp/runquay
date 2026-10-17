# Collective Learnings

Turn experience across projects and AI tools into practical lessons you can reuse.
Topics are open-ended: SEO, security, DNS, DevOps, accessibility, deployment,
customer research, or anything else supported by your past work.

For example, after working on SEO for 20 products, collect their reports under
**SEO**. The AI can suggest recurring checks, techniques, mistakes and tradeoffs,
with references to the work behind each suggestion. It must not invent ranking
gains or treat a repeated claim as proof.

## Collect lessons

1. Open **Learnings** in the sidebar. Choose **Collect learnings from past work**.
2. Enter a topic or tag. Choose a connected analysis tool: Codex, Claude Code or
   Gemini CLI. You can optionally describe what to look for.
3. Search your past work by topic or project. Select individual summaries, or
   choose **Select shown** for up to 100 visible matches. The source-tool filter
   lets you include one tool or combine several.
4. Choose **Review selected information**. Read the exact source snapshot. Close
   the review and uncheck any source you do not want sent to the AI.
5. Acknowledge the reviewed information, then choose **Queue analysis**.
6. If work is paused, choose **Start queued work** when ready. This starts the
   existing queue too. Check Home for any account or billing approval.
7. Review the resulting lesson cards. Expand **When to use it, caveats and
   sources**. Edit an inaccurate or overly specific lesson, dismiss an unhelpful
   one, and choose **Save learning** for useful advice.

Nothing is sent to an AI when you open the page, search sources or prepare the
preview. Queuing requires explicit source-review acknowledgement. The worker
uses the reviewed snapshot; changed sources require another review before
queuing. Repeating the same request does not create another analysis job.

## Use lessons in another project

Choose **Use in a new task** on a saved card, or open a task form and expand
**Use collective learnings (optional)**. Check up to 12 saved lessons, then
describe the new task as usual. Existing-project task forms and reviewed idea
forms support the same selection.

Only the chosen lesson texts, applicability, caveats, confidence labels and tags
are copied into the task. The original source summaries and source project
names are not copied. This is a fixed snapshot: editing or dismissing the library
entry later does not change a task that already received it. Editing a library
entry returns it to review before it can be selected for future tasks.

Saved advice remains untrusted reference material. It cannot override the task,
workspace instructions, privacy rules or required approvals. You can also copy
a lesson's visible text manually into an original AI tool; Runquay does not
silently edit vendor memory files, instructions or native conversations.

## Tags and review

The collection topic becomes the first tag. The AI can propose additional tags,
and you can edit them. There is no fixed category list. Search the library or
filter by topic and **Needs review** / **Saved by you**.

Cards distinguish **reported** observations from **hypotheses**. Neither label
means independently verified. Every card must cite at least one source from its
collection. Invalid source references reject the result rather than partially
saving it. Identical topic/title/lesson suggestions are deduplicated; an empty
result is valid when there is not enough useful evidence.

## Sources, limits and privacy

- Sources include available local Codex, Claude Code, Gemini and Antigravity chat
  titles/previews, compatible imported metadata from other tools, and completed
  Runquay step reports with their reported checks. Refresh native histories in
  **Tasks**, then choose **Refresh summaries** here.
- Native previews may contain only an initial request. They do not establish
  what the tool ultimately did. Full native transcripts, raw logs, credentials,
  arbitrary project files and cloud-only history are not ingested by this
  feature. Better reports produce better lessons.
- One collection accepts 1–100 sources and at most 120,000 serialized context
  characters. The source picker shows up to 100 search matches at a time. Source
  discovery offers up to 1,000 recent native/imported records and 500 completed
  Runquay step reports. The library shows up to 500 recent active cards and the
  latest 30 collection jobs; older records remain in the private database.
- Source context is minimized with best-effort credential, email and local-path
  removal. This is not a privacy guarantee: project names, proprietary details
  or unfamiliar secret formats may remain. Always review the snapshot.
- Selected summaries go to the chosen provider through its official CLI.
  Collections and lessons live in Runquay's excluded private data directory.
  No public upload, telemetry or publication is part of this workflow.
- Codex keeps its subscription/quota and zero-paid-credit checks. Claude and
  Gemini still require a separate approval for every invocation because their
  billing is not verified by Runquay. No credits or resets are purchased.
- Analysis uses existing read-only adapters and asks the model to use only the
  supplied snapshot. Native CLI permission controls are not a guarantee of
  total filesystem or network containment. Antigravity/custom histories can be
  sources, but those adapters cannot analyze collections until a supported
  read-only mode is established. No permission-bypass mode is added.

See [tool verification limits](TOOLS.md), [daily workflows](WORKFLOWS.md), and
[privacy and security](../SECURITY.md).
