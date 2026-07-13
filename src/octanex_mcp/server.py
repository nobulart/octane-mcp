from __future__ import annotations

import argparse
import json
from typing import Any, Dict, Optional

from .bridge import (
    Workspace,
    concept_to_commands,
    create_simple_obj,
    flush_queue,
    list_commands,
    octane_app_status,
    probe_types as _probe_types,
    read_recipe_book,
    read_status,
    record_recipe_entry,
    scene_harvest as _scene_harvest,
    write_command,
)
from .bridge_control import octane_process_status, reset_octane_scene, run_bridge_script
from .config import doctor, initialize_environment, resolve_config
from .recipes import load_recipe, queue_recipe, recipe_index, validate_recipe_library
from .corpus import find_grammar
from .api_corpus import inspect_command
from .review import review_preview, suggest_camera_fix, suggest_lighting_fix
from .schema import command_schema, validate_command, validate_queue
from .models import DEFAULT_QUALITY, QUALITY_TIERS
from .scene import add_scene_object, load_scene_manifest, queue_scene_plan, remove_scene_object, requeue_scene, save_scene_manifest, swap_geometry, update_scene_object, group_objects, modify_objects, animate_objects
from .sanity import analyze_scene_graph, analyze_scene_plan
from .annotation import compute_label_layout, CameraView, draw_label_overlay
from .visuals import camera_for_bounds, create_avatar_face_obj, create_bar_chart_obj, create_scatter_obj, create_surface_obj, scene_commands_for_asset
from .pointcloud import PointCloudDependencyError, PointCloudFormatError, point_cloud_to_asset, particle_cloud_scene_commands, supported_point_cloud_formats
from .geo import geojson_to_obj, geo_asset_to_scene_commands, GeoDependencyError
from .animation import orbit_manifest, build_animation_commands

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - exercised when deps are missing
    FastMCP = None  # type: ignore


def _json(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=2)


# Per-agent identity for the scheduler (host:pid, override via OCTANEX_AGENT_ID).
from .scheduler import agent_id as _agent_id  # noqa: E402

def _build_save_preview_envelope(
    *,
    path: Optional[str] = None,
    width: int = 1280,
    height: int = 1280,
    samples: int = 64,
    min_samples: int = 16,
    timeout_seconds: int = 10,
    quality: Optional[str] = None,
    max_render_time: Optional[int] = None,
    progressive: bool = False,
) -> Dict[str, Any]:
    """Resolve a ``save_preview`` command envelope.

    Shared by the MCP tool and the HTTP gateway so both stay in parity.
    ``progressive=True`` additionally emits an early low-spp frame at
    ``preview_progressive.png`` before the final frame (see bridge C1).

    Convergence defaults follow ``DEFAULT_QUALITY`` (the ``fast`` tier,
    500 s/px). Octane X ships a film ``maxSamples`` of 5000, so a
    caller that passes no samples/quality would otherwise inherit Octane's own
    5000-s/px crawl; the bridge overrides the film's maxSamples with
    the command's ``samples`` on every render, but only if we emit one.
    The default here therefore bakes in 500 s/px so a scene builds and
    renders in 1-3 s rather than crawling to full convergence.
    """
    tier = None
    if quality:
        if quality not in QUALITY_TIERS:
            raise ValueError(f"quality must be one of {sorted(QUALITY_TIERS)}")
        tier = QUALITY_TIERS[quality]
    else:
        tier = QUALITY_TIERS.get(DEFAULT_QUALITY)
    resolved = {
        "path": path,
        "width": width,
        "height": height,
        "samples": samples if samples != 64 else (tier["samples"] if tier else 64),
        "min_samples": min_samples if min_samples != 16 else (tier["min_samples"] if tier else 16),
        "timeout_seconds": timeout_seconds if timeout_seconds != 10 else (tier["timeout_seconds"] if tier else 10),
        "max_render_time": max_render_time if max_render_time is not None else (tier["max_render_time"] if tier else None),
        "quality": quality or None,
        "progressive": bool(progressive),
    }
    if progressive:
        from .bridge import Workspace

        resolved["progressive_path"] = str(Workspace().renders_dir / "preview_progressive.png")
    return resolved


def build_mcp() -> Any:
    if FastMCP is None:
        raise RuntimeError("mcp package is not installed. Run: uv sync")

    mcp = FastMCP("octanex-mcp")

    @mcp.tool()
    def octane_status() -> str:
        """Return Octane X app, bridge heartbeat, and command queue status."""
        return _json({"app": octane_app_status(), "commands": list_commands()})

    @mcp.tool()
    def octane_capabilities() -> str:
        """Report Octane X capability/version from the live API corpus.

        Reads the most recent OctaneMCP/octane_lua_api.<build>.json
        (emitted by export_api_docs_v3.lua inside Octane X) and
        returns: which Octane build is in play, which runtime probes
        (scene graph, node.create, render.start, saveImage, statistics)
        actually exist, which key constants (node types, pins, maxSamples)
        are present, the bridge's implied lighting strategy, and whether
        the known-good save_preview signature is available. This is the
        "what does THIS build support" answer so the agent never has
        to guess against hardcoded folklore.
        """
        from .api_corpus import inspect_command
        return _json(inspect_command())

    @mcp.tool()
    def octane_api_corpus_export() -> str:
        """Instructions for producing the live Octane X API corpus.

        Octane X has no CLI entry point (docs/octane-x-no-cli.md), so
        the corpus exporter runs from the in-app Scripts menu, not a
        shell. This returns the script to fire and where the JSON lands.
        """
        from .api_corpus import export_command
        return _json(export_command())

    @mcp.tool()
    def octane_probe_types() -> str:
        """Probe live which Octane node types the running build supports.

        Queues the bridge's probe_types command, which tests each candidate
        NT_* constant (NT_LIGHT_AREA/SUN/DAYLIGHT, NT_ENV_TEXTURE/RGB, NT_GEO_*,
        etc.) for existence + create-ability and enumerates the daylight
        environment node's attribute pins. Complements octane_capabilities
        (the offline export): this is the exact running-build answer to
        "can the bridge build a real dark_studio / light here?". Returns the
        probe result dict once the persistent bridge drains it.
        """
        return _json(_probe_types())

    @mcp.tool()
    def octane_scene_harvest() -> str:
        """Harvest the live OctaneX scene graph in real time.

        This queries the running OctaneX application directly (via the persistent
        Lua bridge's scene_graph() API) and returns all scene nodes as a JSON
        array of node objects. Each node includes:
          - name: the node's display name
          - type: the node type (camera, mesh, material, light, etc.)
          - position: [x, y, z] in world coordinates
          - scale: [x, y, z] scale factors
          - rotation: [rx, ry, rz] rotation (if available)
          - has_geometry: boolean — does this node have mesh geometry?
          - has_material: boolean — is a material connected?
          - connected: list of connected node names (if applicable)

        This is the tool the agent uses to see what the user is working on
        in the OctaneX viewport — camera position, scene objects, materials,
        all live. The agent can call this after the user moves the camera,
        adds objects, or modifies the scene to get a fresh snapshot.
        """
        result = _scene_harvest()
        return _json(result)

    @mcp.tool()
    def octane_scene_sanity(strict: bool = False) -> str:
        """Sanity-check the LIVE OctaneX node graph before rendering.

        Harvests the running scene graph (via octane_scene_harvest) and runs a
        graph-level sanity gate: render-target presence, camera present + wired to
        the render target, at least one light/environment, meshes with geometry and
        an assigned material, orphan materials, and zero/negative node scales.
        This is a pre-render guard that catches dangling/orphaned/broken nodes
        BEFORE spending GPU on save_preview — complementary to the post-render
        pixel QA in octane_review_preview.

        Returns a report with ok / error_count / warning_count / issues[] (each
        issue carries severity, code, message, and the offending node when known).
        It never mutates the scene or blocks the render — the agent decides whether
        to proceed. Set strict=True to escalate likely-blank signals (no lighting,
        camera not wired) from warnings to errors.
        """
        harvest = _scene_harvest()
        report = analyze_scene_graph(harvest, strict=strict)
        return _json({"harvest_count": harvest.get("count"), **report.as_dict()})

    @mcp.tool()
    def octane_check_scene_plan(scene_plan: Dict[str, Any], strict: bool = False) -> str:
        """Sanity-check a scene MANIFEST before building/queueing it.

        Runs the offline graph gate against the planned scene (objects, materials,
        camera, lighting) plus precise camera-framing math using the per-object
        bounds the OBJ generator attaches. Catches errors even earlier than
        octane_scene_sanity — before a single command is queued.

        Examples of what it flags: no camera / invalid camera vectors, mesh objects
        with no geometry path, materials that no object references, zero/negative
        scale transforms, no light/environment, and a camera that is inside,
        too far from, or too close to the subject (empty/clipped frames).

        Returns a report with ok / error_count / warning_count / issues[]. Report-only:
        it does not build or render. Set strict=True to treat missing lighting as an
        error rather than a warning.
        """
        report = analyze_scene_plan(scene_plan, strict=strict)
        return _json(report.as_dict())

    @mcp.tool()
    def octane_bridge_process_status() -> str:
        """Return Octane X process state, generated bridge paths, and bridge heartbeat age."""
        return _json(octane_process_status())

    @mcp.tool()
    def octane_run_bridge(mode: str = "oneshot", dry_run: bool = False, timeout_seconds: int = 30) -> str:
        """Run a generated Octane bridge script from the Scripts menu via AppleScript.

        Launches Octane X if needed, waits for its menu bar to become UI-ready,
        then clicks the bridge from the Scripts menu. A single oneshot click
        drains the ENTIRE queue (the Lua drain loop re-snapshots until empty),
        so call this once after queueing a full pipeline — not once per command.
        """
        return _json(run_bridge_script(mode, dry_run=dry_run, timeout_seconds=timeout_seconds))

    @mcp.tool()
    def octane_run_oneshot_bridge(dry_run: bool = False, timeout_seconds: int = 30) -> str:
        """Run hermes_bridge_oneshot.generated.lua via AppleScript for batch queue draining.

        A single click drains the whole queue. After this returns ok, poll the
        workspace queue/ for 0 files and wait for the preview PNG to be written.
        Do NOT re-click while the queue is empty — that would restart/kill the
        in-progress save_preview render.
        """
        return _json(run_bridge_script("oneshot", dry_run=dry_run, timeout_seconds=timeout_seconds))

    @mcp.tool()
    def octane_start_persistent_bridge(dry_run: bool = False, timeout_seconds: int = 30) -> str:
        """Run hermes_bridge_persistent.generated.lua via AppleScript to open/manage the persistent bridge."""
        return _json(run_bridge_script("persistent", dry_run=dry_run, timeout_seconds=timeout_seconds))

    @mcp.tool()
    def octane_reset_octane_scene(timeout_seconds: int = 20) -> str:
        """Warm-engine reset: File > New on the running Octane X (clears the in-memory scene graph).

        Required between recipes so request_render_restart does not wedge on
        stale scene nodes. Prefer this over a cold quit/open-a relaunch, which
        leaves the render engine cold and re-wedges the drain. Returns an ok
        flag plus a failure class (tcc_denied / busy / script_not_found) so the
        caller can branch instead of blindly retrying.
        """
        return _json(reset_octane_scene(timeout_seconds=timeout_seconds))

    @mcp.tool()
    def octane_recipe_book(limit_chars: int = 12000) -> str:
        """Read the local OctaneX MCP recipe book of successes, failures, and reusable patterns."""
        return _json(read_recipe_book(limit_chars=limit_chars))

    @mcp.tool()
    def octane_record_recipe(
        title: str,
        outcome: str,
        context: str,
        steps: list[str],
        signals: Optional[list[str]] = None,
        follow_ups: Optional[list[str]] = None,
    ) -> str:
        """Append a compact success/failure note to docs/recipe-book.md for future agents."""
        return _json(record_recipe_entry(
            title=title,
            outcome=outcome,
            context=context,
            steps=steps,
            signals=signals or [],
            follow_ups=follow_ups or [],
        ))

    @mcp.tool()
    def octane_recipe_index() -> str:
        """List checked-in example recipes with normalized metadata and preview/native verification status."""
        return _json(recipe_index())

    @mcp.tool()
    def octane_load_recipe(slug: str) -> str:
        """Load a checked-in recipe by slug, including command sequence and resolved asset paths."""
        return _json(load_recipe(slug))

    @mcp.tool()
    def octane_queue_recipe(slug: str, overrides: Optional[Dict[str, Any]] = None) -> str:
        """Queue a checked-in recipe command sequence by slug, with optional per-op payload overrides."""
        return _json(queue_recipe(slug, overrides=overrides or {}))

    @mcp.tool()
    def octane_validate_recipe_library() -> str:
        """Validate checked-in recipe metadata, required files, previews, and command payloads."""
        return _json(validate_recipe_library())

    @mcp.tool()
    def octane_find_grammar(query: str, top_k: int = 3, domain: Optional[str] = None,
                            only_converged: bool = False) -> str:
        """WP9 RAGS retrieval: find the nearest existing corpus grammar to warm-start a new subject.

        Searches the harvested reference corpus (``corpus/``) for entries whose
        labels / domain / subject / title / dominant colors match ``query``.
        Returns ranked matches, each carrying its pixel-derived ``derived_acceptance``
        spec so a new render can be conditioned against the closest prior reference.
        Pure offline ranking: keyword + hue-overlap + era, no embeddings, no network.

        Args:
            query: free-text subject, e.g. "red sphere" or "blue ceramic vase".
            top_k: max matches to return (default 3).
            domain: optional domain filter (e.g. "photoreal", "stylized").
            only_converged: if true, only return entries that have a rendered preview.
        """
        return _json(find_grammar(query, top_k=top_k, domain=domain,
                                  only_converged=only_converged))

    @mcp.tool()
    def octane_validate_command(command: Dict[str, Any]) -> str:
        """Validate one JSON command envelope before it is queued or replayed."""
        result = validate_command(command)
        return _json({"ok": result.ok, "errors": result.errors, "warnings": result.warnings, "error_details": result.error_details})

    @mcp.tool()
    def octane_schema() -> str:
        """Return the supported command schema, operation list, limits, and examples."""
        return _json(command_schema())

    @mcp.tool()
    def octane_validate_queue() -> str:
        """Validate all queued command JSON files in the current workspace."""
        return _json(validate_queue(Workspace()))

    @mcp.tool()
    def octane_flush_queue(backup: bool = True) -> str:
        """Flush the command queue before a live render.

        The container queue is shared and persistent; prior sessions can leave
        thousands of stale commands that would otherwise re-render on drain.
        This MOVEs queued files into a dated backup dir (never deletes) so the
        operation is recoverable, then returns how many were cleared.

        OPERATOR ESCAPE HATCH ONLY. When the scheduler is in use, prefer
        ``octane_submit_job`` + ``octane_job_status`` — flushing destroys other
        agents' pending work instead of queueing it.
        """
        return _json(flush_queue(Workspace(), backup=backup))

    @mcp.tool()
    def octane_submit_job(
        commands: list[dict],
        agent_id: Optional[str] = None,
        preview_path: Optional[str] = None,
    ) -> str:
        """Stage a complete render job (a full scene build) and queue it behind
        the shared-engine lock so multiple agents can share Octane X safely.

        ``commands`` is a list of command envelopes (each with ``op``/``payload``).
        They are NOT written into the global ``queue/`` immediately; they are
        staged under ``jobs/<job_id>/commands`` and promoted onto the engine by
        the dispatcher (``octane_dispatch_jobs``) under a filesystem lease lock.

        Submission never flushes other agents' work. Use ``octane_job_status``
        to poll state and output paths, and ``octane_job_queue`` to see waiting
        jobs. This is additive — the classic ``octane_*`` queue tools still drain
        the global queue directly for single-agent use.
        """
        from .scheduler import JobScheduler

        sched = JobScheduler.from_defaults(agent_id or _agent_id())
        job_id = sched.submit(commands, agent_id=agent_id or _agent_id(), preview_path=preview_path)
        position = None
        for i, j in enumerate(sched.queued_jobs()):
            if j["job_id"] == job_id:
                position = i
                break
        return _json({
            "ok": True,
            "job_id": job_id,
            "queue_position": position,
            "status": "queued",
            "preview_path": preview_path,
        })

    @mcp.tool()
    def octane_job_status(job_id: str) -> str:
        """Poll a submitted job's state: queued -> active -> done/failed.

        Completion is filesystem-observable (``jobs/<id>/done.json``), so it
        keeps working even if the controlling drain process was killed. Returns
        the manifest, lock state, and any output paths recorded on completion.
        """
        from .scheduler import JobScheduler

        sched = JobScheduler.from_defaults(_agent_id())
        manifest = sched.get_manifest(job_id)
        if manifest is None:
            return _json({"ok": False, "error": f"no such job: {job_id}"})
        done = None
        done_path = sched.jobs_dir / job_id / "done.json"
        if done_path.exists():
            try:
                done = json.loads(done_path.read_text(encoding="utf-8"))
            except Exception:
                done = None
        return _json({
            "ok": True,
            "manifest": manifest,
            "done": done,
            "lock": sched.lock.state(),
            "is_done": sched.is_done(job_id),
        })

    @mcp.tool()
    def octane_job_queue() -> str:
        """Snapshot of all jobs (queued / active / done / failed) and the
        current render-lock state. Use it to decide whether to submit or wait.
        """
        from .scheduler import JobScheduler

        sched = JobScheduler.from_defaults(_agent_id())
        return _json({
            "jobs": sched.list_jobs(),
            "lock": sched.lock.state(),
            "global_queue_files": [p.name for p in sched.pending_queue_files()],
        })

    @mcp.tool()
    def octane_dispatch_jobs(max_retries: int = 5) -> str:
        """Promote the oldest queued job onto the engine under the shared lock
        and acquire the lease. This is the ONLY path that writes to the global
        ``queue/`` and triggers a drain, so it must be the sole caller — both the
        MCP tools and any hand-rolled ``osascript octane_drain.applescript`` must
        go through it, or check ``octane_job_queue().lock`` first.

        Returns the promoted ``job_id`` (now draining), or ``null`` if the engine
        is busy (a live lease held by another agent) or nothing is queued.
        """
        from .scheduler import JobScheduler

        sched = JobScheduler.from_defaults(_agent_id())
        promoted = sched.dispatch_cycle(max_retries=max_retries)
        return _json({
            "promoted_job_id": promoted,
            "lock": sched.lock.state(),
            "queued": sched.queued_jobs(),
        })

    @mcp.tool()
    def octane_render_job(
        timeout_seconds: int = 240,
        max_retries: int = 5,
    ) -> str:
        """End-to-end shared-engine render: promote the oldest queued job under
        the lock, run the one-shot Lua drain, and write ``jobs/<id>/done.json``.

        This is the SINGLE render path that multiple agents should use so the
        engine is never double-driven. Completion is filesystem-observable, so
        even if THIS process is SIGTERM'd mid-render the job is resolvable by the
        next agent (see ``octane_job_status``). On a hard drain failure the job
        is marked failed and the lock released for retry.

        Returns {promoted_job_id, drain, done, lock}. If the engine is busy
        (another agent holds a live lease) or nothing is queued, promoted_job_id
        is null.
        """
        from .scheduler import JobScheduler

        sched = JobScheduler.from_defaults(_agent_id())
        result = sched.dispatch_and_drain(timeout_seconds=timeout_seconds, max_retries=max_retries)
        return _json(result)

    @mcp.tool()
    def octane_ping(message: str = "hello from Hermes") -> str:
        """Queue a ping command for the Octane Lua bridge."""
        return _json(write_command("ping", {"message": message}))

    @mcp.tool()
    def octane_create_test_cube(name: str = "mcp_cube", size: float = 1.0) -> str:
        """Create a small OBJ cube asset and queue an import_geometry command."""
        asset = create_simple_obj(name=name, size=size)
        queued = write_command("import_geometry", {"path": asset["path"], "format": "obj", "name": asset["name"]})
        return _json({"asset": asset, "command": queued})

    @mcp.tool()
    def octane_import_geometry(path: str, name: Optional[str] = None, format: str = "auto") -> str:
        """Queue an import_geometry command for OBJ/USD/FBX/Alembic/etc."""
        return _json(write_command("import_geometry", {"path": path, "format": format, "name": name}))

    @mcp.tool()
    def octane_create_material(
        name: str,
        kind: str = "glossy",
        color: Optional[list[float]] = None,
        roughness: float = 0.25,
        metallic: float = 0.0,
        transmission: float = 0.0,
        ior: float = 1.5,
        opacity: float = 1.0,
        clearcoat: float = 0.0,
        anisotropy: float = 0.0,
        emission: float = 0.0,
        texture_path: Optional[str] = None,
        normal_path: Optional[str] = None,
    ) -> str:
        """Queue a material creation/update command with optional PBR fields.

        Any non-default PBR field is forwarded to the bridge. Octane pins that
        are unavailable on the current build are acknowledged with a warning by
        the Lua handler rather than crashing the command.
        """
        payload: dict[str, Any] = {
            "name": name,
            "kind": kind,
            "color": color or [0.8, 0.8, 0.8],
            "roughness": roughness,
            "metallic": metallic,
        }
        if transmission:
            payload["transmission"] = transmission
        if ior != 1.5:
            payload["ior"] = ior
        if opacity != 1.0:
            payload["opacity"] = opacity
        if clearcoat:
            payload["clearcoat"] = clearcoat
        if anisotropy:
            payload["anisotropy"] = anisotropy
        if emission:
            payload["emission"] = emission
        if texture_path:
            payload["texture_path"] = texture_path
        if normal_path:
            payload["normal_path"] = normal_path
        return _json(write_command("create_material", payload))

    @mcp.tool()
    def octane_create_light(
        name: str,
        light_type: str = "area_light",
        intensity: float = 10.0,
        position: Optional[list[float]] = None,
        direction: Optional[list[float]] = None,
        size: Optional[list[float]] = None,
        angle: float = 45.0,
        hdr_path: Optional[str] = None,
    ) -> str:
        """Queue a native light creation command (area, sun, environment, emissive, etc.).

        The bridge creates the matching Octane light/environment node and wires it
        to the active render target, acking unsupported pins with a warning.
        """
        payload: dict[str, Any] = {
            "name": name,
            "light_type": light_type,
            "intensity": intensity,
        }
        if position:
            payload["position"] = position
        if direction:
            payload["direction"] = direction
        if size:
            payload["size"] = size
        if light_type == "sun_light":
            payload["angle"] = angle
        if light_type == "environment" and hdr_path:
            payload["hdr_path"] = hdr_path
        return _json(write_command("create_light", payload))

    @mcp.tool()
    def octane_assign_material(object_name: str, material_name: str) -> str:
        """Queue a material assignment command."""
        return _json(write_command("assign_material", {"object_name": object_name, "material_name": material_name}))

    @mcp.tool()
    def octane_set_camera(position: list[float], target: list[float], fov: float = 45.0) -> str:
        """Queue a camera placement command."""
        return _json(write_command("set_camera", {"position": position, "target": target, "fov": fov}))

    @mcp.tool()
    def octane_set_lighting(preset: str = "soft_studio") -> str:
        """Queue a lighting preset command."""
        return _json(write_command("set_lighting", {"preset": preset}))

    @mcp.tool()
    def octane_start_render(samples: int = 128, width: int = 1280, height: int = 1280) -> str:
        """Queue a render start/restart command."""
        return _json(write_command("start_render", {"samples": samples, "width": width, "height": height}))

    @mcp.tool()
    def octane_save_preview(
        path: Optional[str] = None,
        width: int = 1280,
        height: int = 1280,
        samples: int = 64,
        min_samples: int = 16,
        timeout_seconds: int = 10,
        quality: Optional[str] = None,
        max_render_time: Optional[int] = None,
        progressive: bool = False,
    ) -> str:
        """Queue a render-ready preview image save command.

        Convergence ceiling: pass ``quality`` to pick a preset tier
        (preview=10s, standard=30s, high=60s, ultra=120s, final=unlimited). Either the
        Octane film ``maxRenderTime`` or the Lua ``timeout_seconds`` poll acts
        as the cap; the render stops at whichever is hit first and the frame is
        saved (best-effort on timeout). Raw ``samples``/``min_samples``/
        ``timeout_seconds``/``max_render_time`` override the tier when given.

        Set ``progressive=True`` to also emit an early low-spp frame at
        ``preview_progressive.png`` before the final frame (bridge C1).
        """
        try:
            resolved = _build_save_preview_envelope(
                path=path,
                width=width,
                height=height,
                samples=samples,
                min_samples=min_samples,
                timeout_seconds=timeout_seconds,
                quality=quality,
                max_render_time=max_render_time,
                progressive=progressive,
            )
        except ValueError as exc:
            return _json({"ok": False, "error": str(exc)})
        return _json(write_command("save_preview", resolved))

    @mcp.tool()
    def octane_review_preview(path: Optional[str] = None) -> str:
        """Review a saved PNG preview for blank/clipped/low-contrast output using image-level QA metrics."""
        preview_path = path or str(Workspace().renders_dir / "preview.png")
        return _json(review_preview(preview_path))

    @mcp.tool()
    def octane_suggest_camera_fix(preview_review: Dict[str, Any], asset_bounds: Dict[str, Any]) -> str:
        """Suggest a camera patch from preview QA output and asset bounds."""
        return _json(suggest_camera_fix(preview_review, asset_bounds))

    @mcp.tool()
    def octane_suggest_lighting_fix(preview_review: Dict[str, Any]) -> str:
        """Suggest a lighting/render patch from preview QA output."""
        return _json(suggest_lighting_fix(preview_review))

    @mcp.tool()
    def octane_build_concept(prompt: str) -> str:
        """Queue a high-level concept build request plus deterministic starter scene commands."""
        results = []
        cube = create_simple_obj(name="concept_anchor_cube", size=1.0)
        results.append(write_command("import_geometry", {"path": cube["path"], "format": "obj", "name": cube["name"]}))
        for cmd in concept_to_commands(prompt):
            results.append(write_command(cmd["op"], cmd["payload"]))
        return _json({"queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_save_scene_manifest(scene_plan: Dict[str, Any]) -> str:
        """Validate and save a semantic scene plan manifest without queueing commands."""
        return _json(save_scene_manifest(scene_plan))

    @mcp.tool()
    def octane_build_scene(scene_plan: Dict[str, Any]) -> str:
        """Build a semantic scene plan: save its manifest and queue validated Octane commands."""
        return _json(queue_scene_plan(scene_plan))

    @mcp.tool()
    def octane_load_scene_manifest(scene_id: str) -> str:
        """Load a saved semantic scene manifest by scene_id."""
        return _json(load_scene_manifest(scene_id))

    @mcp.tool()
    def octane_add_object(scene_id: str, object_spec: Dict[str, Any]) -> str:
        """Add one object to a saved scene manifest and resave it."""
        return _json(add_scene_object(scene_id, object_spec))

    @mcp.tool()
    def octane_update_object(scene_id: str, object_id: str, changes: Dict[str, Any]) -> str:
        """Update one object in a saved scene manifest and resave it."""
        return _json(update_scene_object(scene_id, object_id, changes))

    @mcp.tool()
    def octane_remove_object(scene_id: str, object_id: str) -> str:
        """Remove one object from a saved scene manifest and resave it."""
        return _json(remove_scene_object(scene_id, object_id))

    @mcp.tool()
    def octane_swap_geometry(
        scene_id: str,
        object_id: str,
        new_path: str,
        format: str = "obj",
        queue: bool = False,
    ) -> str:
        """Hot-swap an object's geometry asset in place, preserving its stable node name.

        The replaceable-asset-files primitive of the streaming data-grammar protocol:
        the scene node identity stays fixed so the mesh can be swapped without rebuilding
        the rest of the scene. The replacement file must already exist on disk. When
        ``queue`` is True, also writes the swap command into the queue so the bridge
        hot-replaces the mesh on the next drain. No Lua/schema change required.
        """
        result = swap_geometry(scene_id, object_id, new_path, format=format, queue=False)
        if queue:
            swap_cmd = result.get("swap_command")
            if swap_cmd:
                result["queued"] = write_command(swap_cmd["op"], swap_cmd["payload"])
        return _json(result)

    @mcp.tool()
    def octane_requeue_scene(scene_id: str) -> str:
        """Load a saved scene manifest and queue its validated commands again."""
        return _json(requeue_scene(scene_id))

    @mcp.tool()
    def octane_annotate_preview(
        scene_id: str,
        source_png: Optional[str] = None,
        out_png: Optional[str] = None,
        width: int = 1280,
        height: int = 1280,
    ) -> str:
        """Dev overlay: draw stable "#N" badges onto a rendered preview.

        Lets the human talk about the scene by number -- "change object #43",
        "group #6 through #10" -- by projecting each labelled object's
        bounds.center through the scene camera and stamping its badge in 2D.

        Render the scene first (octane_build_scene / octane_save_preview), then
        call this on the produced PNG. If ``source_png`` is omitted it defaults
        to the workspace ``renders/octane-preview.png``. The output defaults to
        ``renders/<scene_id>_annotated.png``.

        Requires Pillow (the ``harvest`` extra) for the raster step. If it is
        missing the tool still returns the computed label layout (badge -> screen
        x/y/depth, visibility) plus a precise install hint, so labelling logic
        is inspectable without the dependency.
        """
        from .bridge import Workspace

        ws = Workspace()
        ws.ensure()
        loaded = load_scene_manifest(scene_id, ws)
        scene = loaded["scene"]

        placements = compute_label_layout(scene, width=width, height=height)
        payload = {
            "scene_id": scene_id,
            "labels": [
                {
                    "badge": p.badge,
                    "uid": p.uid,
                    "screen": [round(p.screen[0], 1), round(p.screen[1], 1)],
                    "depth": round(p.depth, 3),
                    "visible": p.visible,
                }
                for p in placements
            ],
            "visible_count": sum(1 for p in placements if p.visible),
        }

        src = source_png or str(ws.renders_dir / "octane-preview.png")
        out = out_png or str(ws.renders_dir / f"{scene_id}_annotated.png")
        from pathlib import Path as _Path
        if not _Path(src).exists():
            payload["error"] = f"source preview not found: {src}"
            return _json(payload)
        try:
            draw_label_overlay(src, placements, out)
            payload["annotated_png"] = out
        except RuntimeError as exc:
            # Missing Pillow (or other raster failure) -> still return layout.
            payload["raster_error"] = str(exc)
        return _json(payload)

    @mcp.tool()
    def octane_group_objects(scene_id: str, refs: str, group_name: Optional[str] = None) -> str:
        """Merge referenced objects into one node (geometry grouping).

        ``refs`` is a human label phrase, e.g. "#6 through #10 and #54". The
        resolved member OBJs are merged into a single asset; the members are
        replaced by the merged node and a "#Gk" group entry is recorded so the
        unit can be addressed later. Requires the optional ``science`` extra
        (trimesh) -> install via ``uv sync --extra science``.
        """
        return _json(group_objects(scene_id, refs, group_name=group_name))

    @mcp.tool()
    def octane_modify_objects(
        scene_id: str,
        refs: str,
        modifier: str,
        iterations: int = 1,
        laplacian: float = 0.5,
        max_faces: Optional[int] = None,
    ) -> str:
        """Apply a mesh modifier to objects by label (Phase 3).

        ``modifier`` is "resolution" (subdivide -> more triangles) or "smooth"
        (Laplacian mesh smoothing). ``refs`` is a label phrase like "#1 and #3"
        or "#G2". Each node keeps its stable name (swap_geometry); only its asset
        is replaced. ``iterations`` controls depth, ``laplacian`` the smoothing
        blend, ``max_faces`` caps subdivision (default 200k). Requires the
        optional ``science`` extra (trimesh) -> ``uv sync --extra science``.
        """
        opts: dict[str, Any] = {"iterations": iterations}
        if modifier.lower() == "smooth":
            opts["laplacian"] = laplacian
        else:
            if max_faces is not None:
                opts["max_faces"] = max_faces
        return _json(modify_objects(scene_id, refs, modifier, **opts))

    @mcp.tool()
    def octane_animate_objects(
        scene_id: str,
        refs: str,
        motion: str,
        axis: str = "y",
        degrees: float = 0.0,
        offset: Optional[list[float]] = None,
        scale: Optional[list[float]] = None,
        start_frame: Any = 0,
        end_frame: Any = 24,
        fps: int = 24,
        easing: str = "ease_in_out_quad",
    ) -> str:
        """Queue a transform animation for objects by label (Phase 4).

        ``motion`` is "rotate" / "translate" / "scale". ``refs`` is a label phrase
        like "#54" or "#6 through #10". For rotate: ``axis`` (x/y/z) + ``degrees``.
        For translate/scale: ``offset`` / ``scale`` as [x,y,z]. ``start_frame`` /
        ``end_frame`` accept ints or timecode strings ("00:00:16:08"); ``fps``
        defaults to 24 (a common standard) when unspecified. ``easing`` supports
        linear / ease_in_out_quad / ease_in_quad / ease_out_quad / ease_in_out_cubic
        -- "rotate #54 by 104 degrees over frames 400-1000 with quadratic in-out"
        maps to motion=rotate, degrees=104, start_frame=400, end_frame=1000,
        easing=ease_in_out_quad.

        Requires the scene nodes to already exist in Octane (build the scene
        first). One click of the one-shot bridge drains the whole per-frame
        set_object_transform + save_preview queue.
        """
        return _json(
            animate_objects(
                scene_id, refs, motion,
                axis=axis, degrees=degrees, offset=offset, scale=scale,
                start_frame=start_frame, end_frame=end_frame, fps=fps, easing=easing,
            )
        )

    @mcp.tool()
    def octane_visualize_bars(values: list[float], name: str = "visual_bar_chart") -> str:
        """Visualize numeric values as a 3D bar chart in Octane."""
        asset = create_bar_chart_obj(values, name=name)
        material_name = f"{asset['name']}_cyan_material"
        commands = scene_commands_for_asset(asset, material_name=material_name, color=[0.05, 0.75, 1.0])
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_visualize_surface(
        expression: str = "sin(r) / max(r, 0.25)",
        name: str = "visual_math_surface",
        x_min: float = -3.0,
        x_max: float = 3.0,
        y_min: float = -3.0,
        y_max: float = 3.0,
        steps: int = 36,
    ) -> str:
        """Visualize z=f(x,y) as a 3D surface. Expression may use x, y, r and safe math funcs."""
        asset = create_surface_obj(expression, name=name, x_range=(x_min, x_max), y_range=(y_min, y_max), steps=steps)
        material_name = f"{asset['name']}_gold_material"
        commands = scene_commands_for_asset(asset, material_name=material_name, color=[1.0, 0.62, 0.12])
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_visualize_scatter(points: list[list[float]], name: str = "visual_scatter_plot") -> str:
        """Visualize xyz points as a 3D scatter plot in Octane."""
        asset = create_scatter_obj(points, name=name)
        material_name = f"{asset['name']}_orange_material"
        commands = scene_commands_for_asset(asset, material_name=material_name, color=[1.0, 0.42, 0.12])
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_visualize_point_cloud(
        source_path: str,
        name: str = "visual_particle_cloud",
        x_column: str = "x",
        y_column: str = "y",
        z_column: str = "z",
        variable: Optional[str] = None,
        time_index: int = 0,
        max_points: int = 512,
        point_size: float = 0.12,
        primitive: str = "sphere",
        color: Optional[list[float]] = None,
    ) -> str:
        """Queue a normalized particle-cloud render from CSV/TSV/XYZ/PTS/ASCII-PLY/JSON/GeoJSON or NetCDF.

        NetCDF is optional and expects a three-dimensional scalar variable (after an
        optional time slice). The strongest finite samples become particles, which is
        a geometry-based volume approximation rather than a physical VDB medium.
        """
        try:
            asset = point_cloud_to_asset(
                source_path,
                name=name,
                columns=(x_column, y_column, z_column),
                variable=variable,
                time_index=time_index,
                max_points=max_points,
                point_size=point_size,
                primitive=primitive,
            )
        except PointCloudDependencyError as exc:
            return _json({"error": str(exc), "hint": "uv sync --extra pointcloud", "queued_commands": [], "supported_formats": supported_point_cloud_formats()})
        except (FileNotFoundError, PointCloudFormatError, ValueError) as exc:
            return _json({"error": str(exc), "queued_commands": [], "supported_formats": supported_point_cloud_formats()})
        preview_path = f"renders/{asset['name']}_octane-preview.png"
        commands = particle_cloud_scene_commands(asset, color=color or [0.08, 0.62, 1.0], preview_path=preview_path)
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "preview_path": preview_path, "queued_commands": results, "status": read_status(), "supported_formats": supported_point_cloud_formats()})

    @mcp.tool()
    def octane_show_avatar(name: str = "hermes_avatar_face") -> str:
        """Show Hermes' geometric avatar face as a scene guide in Octane."""
        asset = create_avatar_face_obj(name=name)
        commands = scene_commands_for_asset(asset, material_name=f"{asset['name']}_warm_light", color=[0.88, 0.95, 1.0])
        commands[3] = {"op": "set_camera", "payload": camera_for_bounds(asset["bounds"], view="front", margin=1.15, fov=38)}
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_visualize_geojson(
        geojson: Dict[str, Any],
        name: str = "visual_geojson",
        z_extrude: float = 0.5,
        color: Optional[list[float]] = None,
    ) -> str:
        """Visualize GeoJSON as extruded geometry in Octane (WP7 geo grammar).

        Accepts a GeoJSON FeatureCollection / Feature / bare geometry DICT. The MCP
        boundary is JSON, so live shapely objects cannot cross it — pass GeoJSON
        dicts here. (The underlying ``geo.geojson_to_obj`` also accepts shapely
        geometries for in-process callers.) Points become marker boxes; lines and
        polygons become extruded walls. Requires the optional `geo` extra (shapely)
        — if it is not installed the tool fails with an exact install hint rather
        than an import traceback.

        Returns the generated asset path, the queued render commands, and the current
        bridge status, so the caller knows the next Octane action required.
        """
        try:
            asset = geojson_to_obj(geojson, name=name, z_extrude=z_extrude)
        except GeoDependencyError as exc:
            return _json({"error": str(exc), "hint": "uv sync --extra geo", "queued_commands": []})
        commands = geo_asset_to_scene_commands(asset, color=color)
        results = [write_command(cmd["op"], cmd["payload"]) for cmd in commands]
        return _json({"asset": asset, "queued_commands": results, "status": read_status()})

    @mcp.tool()
    def octane_build_animation(
        center: list[float] = [0.0, 0.0, 0.0],
        radius: float = 8.0,
        orbit_height: float = 2.0,
        fps: int = 24,
        duration: float = 6.0,
        start_deg: float = 0.0,
        end_deg: float = 360.0,
        fov: float = 45.0,
        segments: int = 24,
        width: int = 1280,
        height: int = 1280,
        samples: int = 64,
        min_samples: int = 16,
        timeout_seconds: int = 10,
        quality: Optional[str] = None,
        max_render_time: Optional[int] = None,
    ) -> str:
        """Queue a camera-orbit animation bake as per-frame commands (WP8).

        Builds a circular camera orbit around ``center`` and queues, for every
        frame, a ``set_camera`` command followed by a ``save_preview`` that writes
        a zero-padded ``frame_XXXX.png`` into the workspace renders dir. The Octane
        Lua bridge drains the queue in order, so running the one-shot renders the
        full clip. No ffmpeg encode here — callers can encode the frames
        afterwards (or inject an encoder via the library model).

        ``quality`` accepts the same tiers as ``octane_save_preview``
        (standard/high/ultra/final); ``max_render_time`` overrides the convergence
        ceiling per frame.
        """
        try:
            manifest = orbit_manifest(
                center=tuple(center),  # type: ignore[arg-type]
                radius=radius,
                height=orbit_height,
                fps=fps,
                duration=duration,
                start_deg=start_deg,
                end_deg=end_deg,
                fov=fov,
                segments=segments,
            )
            preview_env = _build_save_preview_envelope(
                width=width,
                height=height,
                samples=samples,
                min_samples=min_samples,
                timeout_seconds=timeout_seconds,
                quality=quality,
                max_render_time=max_render_time,
            )
            frame_cmds = build_animation_commands(
                manifest,
                width=preview_env["width"],
                height=preview_env["height"],
                samples=preview_env["samples"],
                min_samples=preview_env["min_samples"],
                timeout_seconds=preview_env["timeout_seconds"],
                quality=preview_env["quality"],
                max_render_time=preview_env["max_render_time"],
            )
        except (ValueError, TypeError) as exc:
            return _json({"ok": False, "error": str(exc)})
        results = [write_command(c["op"], c["payload"]) for c in frame_cmds]
        return _json(
            {
                "ok": True,
                "frames": len(results) // 2,
                "queued_commands": results,
                "status": read_status(),
            }
        )

    # ----------------------------------------------------------------------
    # WP6 — promoted recipe tools (first-class wrappers over checked-in recipes)
    #
    # These hide the underlying recipe slug so a downstream agent / Canvas UI can
    # call by semantic name without knowing `examples/recipes/*` internals. Each
    # is a thin wrapper over `queue_recipe` (offline-testable: it only writes
    # command files to the workspace queue).
    # ----------------------------------------------------------------------
    _PLANET_RECIPES = {"earth": "photoreal-earth-space", "saturn": "saturn-moons-space"}

    def _resolve_promoted_slug(recipe_kind: str, planet: Optional[str] = None) -> str:
        if recipe_kind == "product_studio":
            return "photoreal-product-studio"
        if recipe_kind == "planet_scene":
            return _PLANET_RECIPES.get((planet or "earth").lower(), "photoreal-earth-space")
        if recipe_kind == "network":
            return "network-graph"
        raise ValueError(f"unknown promoted recipe kind: {recipe_kind!r}")

    @mcp.tool()
    def octane_build_product_studio(overrides: Optional[Dict[str, Any]] = None) -> str:
        """Queue the Photoreal Product Studio recipe as a first-class tool (WP6)."""
        return _json(queue_recipe(_resolve_promoted_slug("product_studio"), overrides=overrides or {}))

    @mcp.tool()
    def octane_build_planet_scene(planet: str = "earth", overrides: Optional[Dict[str, Any]] = None) -> str:
        """Queue a photoreal planet scene (WP6). `planet='earth'` -> photoreal-earth-space, 'saturn' -> saturn-moons-space."""
        slug = _resolve_promoted_slug("planet_scene", planet=planet)
        return _json(queue_recipe(slug, overrides=overrides or {}))

    @mcp.tool()
    def octane_visualize_network(overrides: Optional[Dict[str, Any]] = None) -> str:
        """Queue the Knowledge Graph / network topology recipe as a first-class tool (WP6)."""
        return _json(queue_recipe(_resolve_promoted_slug("network"), overrides=overrides or {}))

    return mcp


def self_test() -> Dict[str, Any]:
    config = resolve_config()
    ws = Workspace.from_config(config)
    ws.ensure()
    cube = create_simple_obj("self_test_cube", 0.5, ws)
    ping = write_command("ping", {"message": "self-test"}, ws)
    return {"ok": True, "app": octane_app_status(config=config), "cube": cube, "ping": ping, "commands": list_commands(ws)}


def _format_doctor(result: Dict[str, Any]) -> str:
    lines = ["OctaneX MCP doctor", "", f"Overall: {'ok' if result.get('ok') else 'needs attention'}", ""]
    config = result.get("config", {})
    lines.extend([
        f"Workspace: {config.get('workspace')}",
        f"Repo root:  {config.get('repo_root')}",
        f"Octane app: {config.get('app_path')}",
        "",
        "Checks:",
    ])
    for check in result.get("checks", []):
        icon = "✓" if check.get("ok") else "✗"
        detail = f" — {check['path']}" if check.get("path") else ""
        message = f" ({check['message']})" if check.get("message") else ""
        lines.append(f"  {icon} {check['name']}{detail}{message}")
    next_steps = result.get("next_steps") or []
    if next_steps:
        lines.extend(["", "Next steps:"])
        lines.extend(f"  - {step}" for step in next_steps)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Octane X MCP server")
    parser.add_argument("command", nargs="?", choices=["init", "doctor", "bridge-status", "run-oneshot", "start-persistent", "api-corpus"], help="run a setup/diagnostic/bridge command instead of starting MCP stdio")
    parser.add_argument("--self-test", action="store_true", help="create workspace and queue a ping without starting MCP stdio")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON for init/doctor/bridge output")
    parser.add_argument("--no-create", action="store_true", help="doctor only: do not create missing workspace folders")
    parser.add_argument("--dry-run", action="store_true", help="bridge commands only: generate AppleScript without running it")
    parser.add_argument("--timeout", type=int, default=15, help="bridge AppleScript timeout in seconds")
    args = parser.parse_args()
    if args.self_test:
        print(_json(self_test()))
        return
    if args.command == "init":
        print(_json(initialize_environment()))
        return
    if args.command == "doctor":
        result = doctor(create=not args.no_create)
        print(_json(result) if args.json else _format_doctor(result))
        return
    if args.command == "bridge-status":
        print(_json(octane_process_status()))
        return
    if args.command == "run-oneshot":
        print(_json(run_bridge_script("oneshot", dry_run=args.dry_run, timeout_seconds=args.timeout)))
        return
    if args.command == "start-persistent":
        print(_json(run_bridge_script("persistent", dry_run=args.dry_run, timeout_seconds=args.timeout)))
        return
    if args.command == "api-corpus":
        if args.json:
            print(_json(inspect_command()))
        else:
            result = inspect_command()
            if not result.get("ok"):
                print("Octane API corpus not found yet.")
                print("  Fire this in Octane X (Scripts menu): export_api_docs_v3.lua")
                print("  Then re-run: octanex-mcp api-corpus --json")
                if result.get("next_steps"):
                    for step in result["next_steps"]:
                        print("   - " + step)
            else:
                cap = result.get("validation", {}).get("capabilities", {})
                print("Octane X API corpus")
                print("  source: " + str(result.get("source_path", "")))
                print("  build : " + str(cap.get("build_tag", "unknown")))
                print("  lighting strategy: " + str(cap.get("lighting_strategy", "?")))
                print("  save_preview signature known: " + str(cap.get("save_preview_signature_known")))
        return
    build_mcp().run()


if __name__ == "__main__":
    main()
