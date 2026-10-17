# Collective Learnings

Turn experience across projects and AI tools into practical lessons you can reuse.
Topics are open-ended: SEO, security, DNS, DevOps, accessibility, deployment,
customer research, or anything else supported by your past work.

For example, after working on SEO for 20 products, collect their reports under
**SEO**. The AI can suggest recurring checks, techniques, mistakes and tradeoffs,
with references to the work behind each suggestion. It must not invent ranking
gains or treat a repeated claim as proof.

## Collect lessons

1. Open **Learnings**. Choose a suggested topic, ask a question such as “What
   worked across my SEO projects?”, or select **Discover patterns** to look across
   recent work. Runquay chooses matching summaries and a connected analysis tool.
2. Review the readable context cards. Remove any summary you do not want sent,
   then choose **Analyze with [tool]**. This button is the consent action; no
   checkbox, JSON inspection or manual queue setup is needed.
3. Lessons appear automatically. Read a lesson and expand its source context when
   helpful. Choose **Keep lesson** for your library or **Use in a task** to keep
   and attach it in one step. The three-dot menu contains editing and hiding.

Topic suggestions use local keyword matches and counts, not AI conclusions.
The starter vocabulary includes SEO, security, DNS, DevOps, testing,
accessibility and performance. Recurring words in your own task titles can
suggest other topics. Any subject can be typed. Matching is lexical with a
small alias vocabulary, not semantic search; if there are no matches, Runquay
asks for a broader topic instead of silently sending unrelated work.

No AI request starts when you open the page, view topic suggestions or prepare
the context. The **Analyze** action authorizes sending the shown snapshot to the
shown provider. Runquay prefers an eligible Codex subscription connection, then
an enabled supported connection. It does not silently switch the reviewed
provider. Claude/Gemini retain their separate per-invocation billing approval.

The selected analysis can run while your build queue is paused. It does not
start unrelated builds or automatic project ideas. The existing single worker,
quota checks and account handling remain in force. You can leave the page and
return for the result. **Pause work** also stops these analyses. A paused or
blocked collection offers **Continue analysis**, which resumes only that
collection; it does not start other paused work. A running analysis can be
cancelled from its progress card.

Changed source context requires another review before sending. Duplicate active
collections of the same context are reused instead of queued again. Source
availability refreshes locally every minute while this page is open. Native
history discovery still follows the existing background refresh schedule.

## Optional controls

Open **Adjust** only if you want to change the AI, add a focus, or **Choose work
yourself**. Search summaries, filter by tool, and select up to 100. **Use automatic
selection** returns to the default flow. Editing the main question also returns
to automatic source selection. Manual controls remain available without being
required for a normal analysis.

## Use lessons in another project

Choose **Use in a task** on any lesson after reading it. This keeps the lesson
and opens a task form with that lesson selected. Or open a task form and expand
**Use collective learnings (optional)** to choose up to 12 kept lessons.
Existing-project task forms and reviewed idea forms support the same selection.
You still describe and submit the task; using a lesson never starts a build by
itself.

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
filter by topic and **New lessons** / **Kept by you**.

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
