# OctaneX Agentic Canvas — Product and Interaction Specification

**Status:** Product-direction specification

**Date:** 2026-07-14

**Audience:** Canvas, gateway, MCP, renderer, and visual-grammar contributors
**Related implementation documents:**
[`canvas-web-ui-build-plan.md`](canvas-web-ui-build-plan.md),
[`canvas-implementation-roadmap.md`](canvas-implementation-roadmap.md),
[`canvas-roadmap.md`](canvas-roadmap.md), and
[`apps/octanex-canvas/SOUL.md`](../apps/octanex-canvas/SOUL.md).

---

## 1. Product objective

The **OctaneX Agentic Canvas** is the primary workspace in which a person and an
agent collaboratively create, inspect, adapt, and evolve models in a responsive
3D environment.

It is not a prompt box attached to a renderer, a static recipe gallery, or a
PNG preview dashboard. It is a shared modelling surface with two complementary
qualities:

1. **Live canvas:** immediate, editable 3D geometry that supports conversation,
   inspection, selection, camera navigation, and incremental change.
2. **Final render:** an explicit, queued Octane X scene build and quality render
   of a chosen live-scene snapshot.

The intended loop is:

```text
observe / discuss / instruct
          ↓
agent understands the live scene and proposed change
          ↓
minimal, inspectable change to the editable live model
          ↓
user and agent review the result together
          ↓
optional explicit render request
          ↓
OctaneX queues, builds, renders, reports real progress
          ↓
verified final appears in the Final panel
          ↓
final result, scene state, and provenance become reusable material
```

The long-term outcome is a fluid visual language between user and agent. As
visual grammars mature, a person should be able to express intent at an
appropriate level—"make the trajectory legible", "compare the null model",
"move the camera to show the relation", "use the previous surface as a base"—
while retaining a concrete, inspectable 3D model rather than receiving an
opaque image.

---

## 2. Product stance

### 2.1 Conversation is the primary control surface

Natural-language interaction is the normal way to propose, refine, and explain
visual work. The user should not need to translate every idea into a scene graph
or a long sequence of low-level controls.

The agent must nevertheless make its interpretation visible:

- identify the scene object(s) or grammar element(s) it refers to;
- distinguish a discussion, a proposed change, a live change, and a render;
- report uncertainty or missing scene references before acting;
- keep each committed edit small, reversible, and attributable.

### 2.2 The live scene is authoritative for collaboration

`canvas.scene.v1` is the editable scene contract and the source of truth for
what the user and agent are collaboratively evolving. The browser hydrates this
scene into real WebGL geometry; it must not substitute a flat preview image for
an editable model.

Recipe loads, imports, procedural grammars, and agent-created scenes all enter
the same live-scene path. A recipe is therefore a reusable starting model, not
an endpoint or an image.

### 2.3 A final render is an intentional snapshot

Octane X is the quality-render tier, not the interactive editor. A final render
is created from an identified live-scene snapshot after an explicit request.
The final panel shows the resulting render and its provenance. It does not
silently replace or mutate the live scene.

This separation protects rapid exploration from render latency and makes the
relationship between model state and rendered output auditable.

### 2.4 Minimal clutter, not minimal capability

The default screen should favour the model itself. The persistent interface is
limited to the command entry point and compact, truthful state. Contextual
surfaces—selection controls, recipe browser, transcript, render details—appear
only when requested or clearly relevant and can be dismissed without losing
work.

Minimalism must not hide important state. When a render is queued, running,
blocked, failed, or complete, the canvas must say so plainly.

### 2.5 Contractual trust and the design ledger

Agentic visual work needs a stronger memory model than chat. OctaneX Canvas
therefore treats the scene as a contractual object: every accepted change should
produce an inspectable revision, every final render should link back to the exact
scene state that produced it, and every agent action should be traceable to a
user instruction, accepted proposal, explicit tool call, or direct manipulation.

The goal is to prevent design drift and false shared memory. The user and agent
should not have to remember what happened; they should be able to inspect it.
The Canvas should make design memory inspectable.

This gives the project a hard rule: no silent mutation. A design may be discussed
freely, but a canonical scene change must leave a ledger entry that says what
changed, why, by whom or by which tool, and which revision now carries that
change.

---

## 3. Core user experience

### 3.1 The three surfaces

| Surface | Purpose | Rules |
|---|---|---|
| **Live** | Responsive, editable 3D workbench. | Always displays real hydrated geometry; supports camera movement, picking, selection, agent edits, and visual review. |
| **Final** | Quality-render result from Octane X. | Shows a completed or in-progress render for a recorded scene snapshot; never pretends to be editable live geometry. |
| **Split** | Compare the current live model against the latest final. | Preserves correct aspect ratio in each pane; makes it easy to see divergence between current work and a prior rendered snapshot. |

The view selector remains available in all modes. If no final frame exists,
Final and Split state this clearly rather than showing a blank or white panel.

### 3.2 Command semantics

The command bar has two deliberately distinct behaviours:

| User input | Expected behaviour |
|---|---|
| Ordinary text | Conversation and design reasoning only. The agent may clarify, analyse the selected object, propose alternatives, or explain the scene. It must not rebuild or render merely because a sentence was submitted. |
| Explicit live-model instruction | Applies a bounded edit or creates a new live scene. Supported explicit verbs should remain unambiguous, e.g. `visualise`, `viz`, or `build`. |
| Explicit render instruction | Queues a quality render of the current scene snapshot, e.g. `render`, or an equivalent clear UI action. |
| Object reference (`@object-id` or selection chip) | Narrows the agent's scope to a real object in the current scene. The agent echoes the resolved id when it commits an edit. |

A plain Enter submission path must always exist. Modified shortcuts improve
speed but cannot be the only way to converse or act.

### 3.3 Agent response contract

Every agent reply belongs to one of four categories and should communicate that
category in plain language:

1. **Discussion** — no scene state changed.
2. **Proposal** — describes a possible change, awaiting an explicit commit when
   appropriate.
3. **Live update** — identifies the object(s) changed and the change applied to
   `canvas.scene.v1`.
4. **Render update** — identifies the snapshot and render task, then reports
   real pipeline state until a final result is available.

The UI should not expose raw tool-call syntax as the primary response. Tool
calls, patches, task identifiers, and scene revisions remain available as
inspectable provenance when needed.

### 3.4 Selection and direct manipulation

Clicking a live object selects it and makes it available to the conversation as
a contextual reference. The inspector may expose concise controls for common,
reversible adjustments such as material colour, opacity, transform, visibility,
and label. These controls must use the same patch path as agent edits so the
live scene stays coherent.

Direct controls are an accelerator, not a competing scene model.

---

## 4. Model lifecycle and provenance

A collaborative model requires a reliable lifecycle.

```text
idea / reference / recipe
        ↓
scene build or live patch
        ↓
canvas.scene.v1 revision
        ↓
(optional) render snapshot
        ↓
OctaneX task and verified final asset
        ↓
review, further patch, reuse, or export
```

### 4.1 Required identity fields

Every live scene revision should carry or be associated with:

- `scene_id` — stable identity of the evolving model;
- `revision_id` or monotonically increasing revision number;
- creation/update timestamps;
- source/provenance (`recipe`, `user`, `agent`, `import`, `grammar`, or a
  composed source);
- a compact human-readable intent/change summary;
- parent revision or snapshot reference where applicable.

Every render task should additionally record:

- `render_id` / task id;
- the exact source `scene_id` and `revision_id` or immutable snapshot hash;
- target/backend and requested quality settings;
- queue and start/completion timestamps;
- output asset path(s);
- verification status and a concise review summary.

This prevents an attractive final image from becoming detached from the live
model that produced it.

### 4.2 Reversibility and history

The canvas should preserve a lightweight revision timeline for committed live
changes and render snapshots. Users need not see a permanent timeline panel,
but the system must support undo/revert, comparison, and recovery after a
restart.

The initial target is revision-level history, not collaborative text-editor
operational transforms. Do not introduce a complex multi-user merge system
before there is a demonstrated need.

### 4.3 Design ledger events

The design ledger is the chronological trust record for the model. It is not a
verbose debug log and should not clutter the default view, but it must be durable
enough to answer, "what changed, from what, because of which instruction, and
what evidence proves the resulting state?"

Ledger events should cover at least:

- `user_instruction` — the user's explicit request or direct manipulation;
- `agent_proposal` — a suggested change that has not yet mutated the scene;
- `proposal_accepted` / `proposal_rejected` — the user's decision;
- `scene_build` — creation or replacement of a live scene;
- `scene_patch` — a bounded change to object, material, camera, annotation, or
  grammar parameter;
- `snapshot_created` — immutable render input captured from a revision;
- `render_task` — queue, bridge, render, save, and verification lifecycle;
- `verification_result` — structural, pixel, or human/vision review result.

Each event should carry a compact summary, timestamp, actor (`user`, `agent`,
`system`, or named tool), affected object ids or semantic handles, source and
target revision ids where applicable, and links to artifacts such as patches,
snapshots, renders, or review records.

Conversation summaries are context, not authority. The canonical truth is the
scene file, ledger event, render task record, verified artifact, and any hashes
or paths needed to reproduce them.

---

## 5. Render orchestration and truthful progress

A render is a queueable stateful process, not a blocking black box.

### 5.1 Render state machine

The canvas should expose the following terminal and non-terminal states:

```text
idle
  → snapshotting
  → queued
  → building_scene
  → dispatching
  → rendering
  → saving_frame
  → verifying
  → complete

Any non-terminal state → cancelled | failed | blocked
```

Not every backend can report every intermediate stage. In that case, report the
most specific real state available; never invent a percentage, an ETA, or a
"nearly done" message.

### 5.2 Realtime progress indicator

While a render is active, the canvas displays a compact task indicator without
obscuring the scene. It must include:

- a legible current stage (`queued`, `building scene`, `rendering`,
  `verifying`, etc.);
- real progress when the backend supplies measurable data, such as samples
  completed / samples target;
- the source model/snapshot identifier on demand;
- a cancel action where cancellation is technically safe;
- a clear failure or blocked explanation, including the next operator action
  when known.

The progress indicator should remain visible across Live, Final, and Split. It
is a property of the current render task, not merely of the Final pane.

### 5.3 Completion and final review

When rendering completes:

1. Save the output as a Final-panel candidate associated with the render task.
2. Run the existing structural/pixel validation before accepting it as a usable
   final.
3. Inspect it with the visual-review path.
4. Mark the task **complete** only if validation and review meet the declared
   result criteria; otherwise expose it as failed or needs-review.
5. Present the verified final in the Final panel, retaining access to its source
   snapshot and review record.

A completed task must not silently force the UI into Final mode. The user may be
working on a newer live revision and should retain control of the view.

---

## 6. Visual grammars and grammar networks

The Canvas is the environment in which reusable visual grammar networks are
progressively developed. A grammar is more than a named recipe: it is a tested
mapping from semantic intent and structured inputs to editable scene elements,
constraints, materials, annotations, camera logic, and an appropriate render
strategy.

### 6.1 Grammar requirements

Each grammar should define:

- **Purpose:** the question or visual problem it helps answer.
- **Inputs:** semantic parameters, data schema, units, reference assets, and
  optional constraints.
- **Scene output:** objects, materials, annotations, camera defaults, and
  stable ids in `canvas.scene.v1`.
- **Interaction affordances:** which parts are intended to be selected, edited,
  or discussed.
- **Validity constraints:** ranges, incompatible parameters, and failure modes.
- **Render policy:** live-only, final-render recommended, or required for the
  intended result.
- **Verification criteria:** how the system determines whether the output is
  legible, non-empty, correctly framed, and faithful to its inputs.
- **Examples:** at least one recipe or fixture usable in Live mode.

### 6.2 Network rather than isolated templates

Grammar networks should compose. For example, a geospatial terrain grammar can
supply a surface to a trajectory grammar; a data grammar can provide a legend
and uncertainty encoding to a scientific geometry scene; a camera grammar can
adapt framing to all of them.

Composition must remain explicit and inspectable. Each contributed grammar
should leave provenance in the scene rather than flattening the model into an
untraceable mesh at the first interaction.

### 6.3 Priority grammar families

The established families remain the practical starting set:

- geometry and explanatory diagrams;
- data, networks, fields, and timelines;
- mathematical surfaces and transformations;
- physics/scientific systems;
- geospatial terrain, globe, and time layers;
- technical/product/studio rendering;
- agent-guided annotations and visual explanation.

New grammars should be developed through small demonstrable scenes, not a large
abstract ontology. A grammar earns promotion when it produces a usable live
scene, accepts constrained variation, survives a render handoff, and has a
clear verification method.

---

## 7. Architecture implications

### 7.1 One scene contract, multiple backends

The current `canvas.scene.v1` contract is the collaboration boundary. The live
WebGL renderer hydrates it immediately; the Octane handoff converts the same
scene into render-ready operations at a controlled boundary (including material
normalisation such as hex to RGB).

The browser must not interpret arbitrary Octane commands, and Octane must not
become the owner of the editable browser scene. Backend-specific state belongs
behind explicit adapters.

### 7.2 Agent context must be scene-aware

For every collaborative turn, the agent should receive a compact current-scene
summary, the selected object when one exists, and—when supplied—a current
viewport screenshot. This enables grounded statements such as "I changed
`fan_blade_12`" and avoids pretending to see or edit an object that is absent.

The context should be small enough for responsive interaction. Full geometry
need not be copied into every prompt; ids, types, labels, transforms, material
summaries, relevant annotations, and a revision id are normally sufficient.

### 7.3 Responsive by default

Live operations should feel immediate or should show a local task state quickly.
The UI must remain interactive while long work occurs. Long-running agent
planning, asset import, Octane bridge invocation, and rendering should be
cancellable where safe and should never freeze the command surface.

### 7.4 Local-first and explicit external actions

The base path must work with local scene state, local WebGL, local assets, and
local rendering infrastructure. Network upload, remote execution, sharing, and
cloud model routing remain explicit choices with clear provenance; they are not
implicit side effects of a scene edit or render.

---

## 8. Interface rules

### Persistent elements

- The live viewport or selected view mode.
- A single command bar with a reliable submit path.
- Compact honest status/task information when work is active.
- A visible way to switch Live, Final, and Split.

### Reveal-on-demand elements

- Recipe/command palette.
- Selection inspector.
- Conversation transcript.
- Scene/revision history.
- Render queue and technical details.
- Model/voice configuration.

### Behavioural constraints

- Do not turn conversational text into a build or render without an explicit
  request.
- Do not load a preview PNG as a substitute for recipe or scene geometry.
- Do not hide a needed route back to Live when Final is selected.
- Do not use a simulated progress bar when no measurement exists.
- Do not let a completed render overwrite a newer live revision.
- Do not expose a control that appears to change the agent when it only changes
  transient browser state; model and voice choices must round-trip through the
  actual Hermes routing/configuration boundary.
- Preserve plain Enter and Ctrl/Command shortcut fallbacks across supported
  browser and native-host environments.

---

## 9. Acceptance criteria

The product direction is met for an interaction slice when all of the following
are demonstrably true:

1. **Collaborative editing:** a user can load or build a live scene, select a
   real object, discuss it, and issue one explicit change; the visible WebGL
   geometry updates from the same authoritative scene revision.
2. **Conversation discipline:** a plain design question does not alter the scene;
   an explicit build/edit command does, and the response identifies the changed
   object or created scene.
3. **Responsive workbench:** the user can orbit, pan, zoom, pick, submit another
   message, and inspect status while a render task is running.
4. **Truthful render lifecycle:** an explicit render creates a snapshot-linked
   queue task. The canvas shows real stages and measurable progress when
   available, permits safe cancellation, and shows a concrete error when blocked
   or failed.
5. **Final separation:** a completed verified render is viewable in Final and
   Split without replacing the editable Live scene. The user can trace the final
   back to its source revision.
6. **Grammar reuse:** at least one grammar-backed recipe loads as real editable
   geometry, accepts a constrained variation, and can be handed to Octane for a
   final render.
7. **Minimal usable interface:** default view remains visually calm; palette,
   inspector, transcript, and technical provenance are available without being
   permanently imposed on the scene.
8. **Recovery:** reopening the canvas restores enough scene, revision, and task
   context to continue the collaboration without re-creating the model from
   scratch.

---

## 10. Delivery sequence

The current implementation should evolve in this order:

1. **Stabilise the collaborative core.** Preserve the Live/Final/Split contract,
   scene-aware conversation, explicit build semantics, selection/patch flow,
   recipe geometry loading, and static-asset reliability.
2. **Make render lifecycle first-class.** Introduce snapshot identity, a
   render-task record, truthful stage/progress mapping, cancellation semantics,
   and Final-panel provenance.
3. **Add durable model continuity and ledger trust.** Persist scene revisions,
   render references, accepted proposals, and compact design-ledger events;
   support restore, revert, and source-of-truth inspection.
4. **Formalise grammar packages.** Give selected grammar families parameter
   schemas, validation, fixtures, examples, and render/verification policy.
5. **Extend the canvas deliberately.** Add geo/Copernicus workflows, richer
   imports, annotations, voice, reference imagery, and other backends only when
   they preserve the shared scene and interaction contracts.

Each step should be delivered with live WebGL verification, route/unit tests
where applicable, and a real render verification whenever the Octane handoff
changes.

---

## 11. Proposed expansions: from responsive canvas to visual co-authoring

The following additions are proposed because they strengthen the collaborative
loop without sacrificing the calm, local-first interface. They are not all
immediate implementation commitments; each should be validated as a small,
measurable slice.

### 11.1 Deliberate interaction lanes

Keep one command bar, but give every submitted turn an internally visible lane:

| Lane | Trigger | Agent permission | Intended result |
|---|---|---|---|
| **Discuss** | Plain language | Analyse and propose only. | Shared understanding without accidental scene churn. |
| **Sketch** | `visualise` / `build` | Create or replace a live working scene. | A fast, editable starting hypothesis. |
| **Refine** | An explicit object/grammar change | Patch only named or resolved scene elements. | Controlled evolution of the current model. |
| **Render** | `render` or explicit action | Snapshot, enqueue, and monitor. | A quality output whose provenance is retained. |

The UI does not need four large buttons. The lane may be inferred from the
existing explicit verbs and shown as a small transcript/status label. Its value
is that both agent and user can always tell what permission was granted.

### 11.2 Agent proposals, never silent initiative

The agent should be able to notice opportunities—an unreadable camera angle,
clashing material, missing legend, ambiguous scale, or a likely grammar
extension—but should normally surface them as compact **proposals**, not make
unrequested alterations.

A proposal contains:

- one-sentence rationale grounded in the visible scene or data;
- a bounded patch or new branch it would create;
- expected visual effect;
- an Apply / Dismiss choice, with no hidden background mutation.

This permits useful agent initiative while preserving the user's authorship and
avoiding the failure mode of an agent that "runs off" to build or render.

### 11.3 Scene branches for visual alternatives

Many visual decisions are comparative rather than incremental: two camera
angles, two uncertainty encodings, a technical and a cinematic material pass,
or competing physical interpretations. Add lightweight named branches from a
scene revision:

```text
main revision r17
  ├─ camera-comparison r17/camera-low
  ├─ camera-comparison r17/camera-orbital
  └─ material-study r17/copper-and-glass
```

A branch should be cheap metadata plus a scene revision, not a separate project.
Live/Split comparison can then compare **two live revisions** as well as
Live-versus-Final. Promotion back to the main line is an explicit user action.

This is especially useful for research visualisation, where an image can make a
hypothesis look stronger than warranted. Branching encourages comparison with a
null, alternative interpretation, or less dramatic framing.

### 11.4 Inspectable design ledger

The ledger should appear as a compact timeline when requested, not as permanent
chrome. A useful first version can show:

```text
rev_007 · applied
Added transparent mantle shell and plume geometry.
Source: accepted proposal proposal_004
Render: final_003.png
Verification: passed

proposal_004 · accepted
Reduce mantle opacity and add plume columns.
```

Selecting an entry should reveal the affected object ids, semantic handles,
patch summary, before/after revision, linked render task, and verification
record. This is the product answer to the Mandela-effect failure mode in AI
collaboration: design memory is inspectable rather than reconstructed from chat.

### 11.5 Semantic handles above raw mesh ids

Raw object ids remain necessary, but grammar-backed scenes should expose a thin
semantic layer: stable named handles such as `earth_surface`, `impact_ring`,
`trajectory_1`, `confidence_band`, or `legend_scale`. A handle may resolve to
one object, a collection, or a constrained parameter.

This gives the user natural referents without hiding implementation detail:

```text
"make the confidence band less dominant"
  → semantic handle: confidence_band
  → constrained patch: opacity / material / ordering
  → concrete affected object ids recorded in provenance
```

The resolver must fail honestly when a phrase is ambiguous. It should never use
semantic convenience to patch an arbitrary nearby mesh.

### 11.6 Preflight review before expensive renders

Before dispatching a high-quality render, the canvas should be able to run a
fast, local **render preflight** against the current live scene:

- scene-contract validation and missing-asset checks;
- camera framing and clipping checks;
- material/lighting plausibility checks where deterministic;
- estimated cost or quality tier when the backend can provide it;
- warnings for labels, legends, or annotations not represented in the final
  render path.

Preflight should report warnings, not become an unnecessary gate for routine
work. It exists to prevent avoidable queue time and to make any deliberate
trade-off visible before a scarce Octane render slot is consumed.

### 11.7 Render queue as a shared, inspectable resource

Octane X is a finite, possibly shared render resource. The Final panel should
therefore grow into a compact render-task view that can show:

- current task, source snapshot, stage, and truthful progress;
- pending tasks in priority order;
- ownership/origin and safe cancellation;
- the latest verified frame for each completed task;
- whether a task was superseded by a newer live revision.

This prepares the canvas for multi-agent scheduling without turning the normal
single-user experience into a job-control dashboard.

### 11.8 Evaluation fixtures for each grammar

A grammar should have both aesthetic examples and behavioural fixtures. For
example, a trajectory grammar needs fixtures for a valid orbit, an invalid
input, an off-origin scene, a dense multi-trajectory view, and an alternative
null-model overlay. Each fixture should specify expected live-scene structure,
framing constraints, and—where practical—a render review target.

This creates a practical regression suite for the visual language itself. It is
how grammar networks become dependable tools rather than a growing collection
of impressive but brittle demonstrations.

## 12. Non-goals

This specification does not require:

- a general-purpose CAD replacement;
- automatic rendering after every conversational turn;
- an opaque text-to-image fallback presented as an Octane result;
- a permanently visible, control-heavy 3D editor interface;
- automatic cloud upload or social sharing;
- an unbounded grammar ontology before real grammars have proven useful;
- a forensic dashboard in the default view; the ledger is durable and
  inspectable, but it should stay quiet until the user asks for it or trust
  requires it;
- multi-user concurrent scene merges before the single user–agent collaboration
  loop is robust.

---

## 13. Decision summary

The Canvas should feel like a shared, evolving visual workspace:

> **Discuss freely. Change the live model deliberately. Record every accepted
> change. Render an explicit snapshot. Show real progress. Keep the model,
> final, ledger, and provenance connected.**

That is the product contract against which future Canvas UI, gateway, agent,
visual-grammar, and Octane orchestration changes should be evaluated.
