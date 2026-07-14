# Licence Scope and Precedence — octanex-mcp

**Effective for releases containing this file.** This document identifies the
licence that controls each part of the repository. A more specific notice in a
subdirectory takes precedence over a general repository-level notice for the
material it expressly covers.

## 1. Core software — Business Source License 1.1

The root [`LICENSE`](LICENSE) applies to the **octanex-mcp Core**: original
source code in this repository except material listed as separately licensed
below.

The Core currently includes the MCP server, command schema, Octane bridge,
shared scene contract, generic renderer backends, generic recipes tooling, and
Canvas-adjacent gateway code that has not yet been moved into a dedicated Canvas
product package.

The root BSL is source-available, not OSI open source. Its rights and Change
Date are defined by the unmodified BSL text and parameters in `LICENSE`.

## 2. Agentic Canvas product — PolyForm Noncommercial 1.0.0

[`apps/octanex-canvas/`](apps/octanex-canvas/) is separately licensed under
[PolyForm Noncommercial 1.0.0](apps/octanex-canvas/LICENSE), except third-party
material that carries its own notice.

This is the protected product surface: the native host, Canvas UI, WebGL
renderer, interaction design, and associated original assets in that directory.
Commercial use requires a separate agreement from the Licensor. The local
[`apps/octanex-canvas/NOTICE.md`](apps/octanex-canvas/NOTICE.md) identifies the
scope and third-party exception currently present in that package.

Canvas-specific server-side orchestration is expected to move into a dedicated,
separately licensed package as it is extracted from the shared gateway. Until a
file is actually moved and marked, it remains Core and is governed by the root
BSL. This document does not retroactively alter the licence of historical
releases.

## 3. Original knowledge and documentation — CC BY-SA 4.0

Original explanatory documentation, research methods, conceptual visual grammar
specifications, tutorials, and diagrams created by the Licensor are licensed
under [Creative Commons Attribution-ShareAlike 4.0 International](LICENSE-KNOWLEDGE.md),
unless a file or directory has a more specific licence notice.

This keeps reusable knowledge in a reciprocal commons: derivatives may be made,
including commercially, but must credit the source and be shared under the same
licence.

## 4. Data, corpus, and derived acceptance material — CC BY-NC-SA 4.0

[`LICENSE-DATA.md`](LICENSE-DATA.md) governs the project data layer: `corpus/`,
datasets, model corpora, and derived acceptance specifications, together with
material explicitly marked as data-layer content. Upstream licences and
attribution obligations continue to apply to each harvested work.

## 5. Third-party material

Third-party material retains its own licence. In particular,
`apps/octanex-canvas/web/vendor/three.module.js` is distributed under the MIT
License as stated in its source header. Nothing in this repository grants more
rights to third-party material than its upstream licence permits.

## 6. Names and marks

No licence in this repository grants rights to use the names `octanex-mcp`,
`OctaneX Agentic Canvas`, or associated logos as a product, service, or
endorsement mark. See [`NOTICE`](NOTICE) and
[`COMMERCIAL-TERMS.md`](COMMERCIAL-TERMS.md).

## 7. Reading the repository correctly

If material is subject to more than one applicable right or obligation—for
example, a Canvas screen that includes a third-party asset—the recipient must
comply with every applicable notice. If the notices appear to conflict, do not
assume a broader grant; contact the Licensor for clarification.
