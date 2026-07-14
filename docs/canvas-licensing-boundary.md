# Agentic Canvas Licensing Boundary

**Status:** Current product/licensing boundary

**Date:** 2026-07-14
**Primary scope notice:** [`../LICENSE-SCOPE.md`](../LICENSE-SCOPE.md)

---

## Objective

The Agentic Canvas is intended to be the primary commercial product surface of
OctaneX: a responsive, user–agent collaborative environment for creating,
adapting, reviewing, and rendering evolving 3D models.

The project simultaneously commits to keeping its original knowledge—methods,
research framing, conceptual grammar specifications, tutorials, and explanatory
materials—in a reusable reciprocal commons. The licensing boundary protects the
maintained product and its commercial operation, not the general human ability
to learn, discuss, or independently implement the underlying ideas.

## Current boundary

| Material | Current licence | Rationale |
|---|---|---|
| `apps/octanex-canvas/**` original material | PolyForm Noncommercial 1.0.0 | Protects the native host, UI, live WebGL workbench, interaction design, and original Canvas assets from commercial reuse without agreement. |
| `apps/octanex-canvas/web/vendor/three.module.js` | MIT, upstream | Vendored third-party dependency; its upstream notice controls. |
| Shared MCP, bridge, generic schema, and current mixed Canvas gateway code | Root BSL 1.1 | Source-available Core until Canvas-specific server code is extracted. |
| Original research/method/tutorial/grammar documentation | CC BY-SA 4.0 | Freely reusable knowledge with attribution and reciprocal sharing. |
| Corpus/data/derived acceptance material | CC BY-NC-SA 4.0 plus upstream terms | Protects curated data and honours upstream attribution/licence constraints. |

## What makes the Canvas commercially distinctive

The commercial product is not only a visual skin. The defensible Canvas product
layer comprises:

1. **Collaborative interaction** — conversation-first scene work, selection,
   semantic handles, safe proposals, and explicit commit/render permissions.
2. **Stateful modelling** — live scene revisions, branches, provenance,
   recoverability, and comparison between alternatives.
3. **Render orchestration** — snapshot identity, queueing, truthful progress,
   verification, cancellation, and Final-panel continuity.
4. **Visual grammar runtime** — parameter validation, semantic mapping,
   composition, fixtures, and agent context for dependable scene evolution.
5. **Product craft** — responsive WebGL, native host behaviour, accessibility,
   minimal interface design, and the tested user experience tying all layers
   together.

## Extraction plan

The server-side pieces above are currently partly interleaved with generic
bridge/gateway functionality. Do not claim they are already protected by the
Canvas package licence until files are physically moved and marked.

When the product boundary is next refactored, create a dedicated package such
as:

```text
src/octanex_mcp/canvas_product/
  __init__.py
  api.py
  agent_context.py
  revisions.py
  render_tasks.py
  semantic_handles.py
  grammar_registry.py
  provenance.py
```

Each original file in that package should carry a short scope header referring
to the package licence. The package should then be added explicitly to
`LICENSE-SCOPE.md`. Generic scene validation, Octane bridge controls, and
interchange formats should stay in the BSL Core unless there is a specific
product reason to move them.

## Product and knowledge rules

- Publish concepts, methods, grammar descriptions, and research claims clearly
  under the knowledge licence where the Licensor owns them.
- Keep data provenance intact. The knowledge licence never overrides a corpus
  asset's upstream licence, attribution, NonCommercial, or ShareAlike terms.
- Do not use a Canvas source-code licence as a substitute for hosted-service,
  asset, or output terms. Those rights require their own agreement where needed.
- Keep the names and logos protected by trademark reservation; a licence to code
  or documentation is not permission to represent a fork as the official Canvas.
- Treat contributors carefully. Before accepting substantial third-party Canvas
  code, obtain a contributor licence agreement or equivalent rights sufficient
  to maintain this commercial/noncommercial split.

## Review triggers

Review this boundary before any of the following:

- moving Canvas server-side code into a new package;
- shipping a hosted Canvas or managed render service;
- accepting external contributions to protected Canvas files;
- distributing premium grammar packs or proprietary assets;
- changing the root Core licence or the Canvas product licence;
- adding a dependency with copyleft or incompatible terms.

This is a product and operational specification, not legal advice. Obtain
qualified legal review before publishing customer-facing commercial terms or
making material licensing changes outside this repository.
