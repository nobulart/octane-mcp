#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_PROMPT = 'Please output JSON only: {"visible_objects":"","materials":"","lighting":"","camera_perspective":"","mismatch_risks":""}'


def _collapse_repetition(text: str) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line in seen:
            continue
        seen.add(line)
        lines.append(line)
    return "\n".join(lines)


def run_glm_ocr_api(image_path: Path, prompt: str, model: str, timeout: int, endpoint: str) -> dict[str, Any]:
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 96},
    }
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"image": str(image_path), "model": model, "returncode": None, "ok": False, "stdout": "", "stderr": f"ollama api review failed: {exc}"}
    return {
        "image": str(image_path),
        "model": model,
        "returncode": 0,
        "ok": True,
        "stdout": _collapse_repetition(str(data.get("response") or "").strip()),
        "stderr": "",
    }


def run_glm_ocr_cli(image_path: Path, prompt: str, model: str, timeout: int) -> dict[str, Any]:
    if not shutil.which("ollama"):
        raise RuntimeError("ollama command not found; install/start Ollama or choose another local reviewer")
    try:
        proc = subprocess.run(
            ["ollama", "run", model, prompt, str(image_path)],
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout: str = exc.stdout if isinstance(exc.stdout, str) else ""
        return {
            "image": str(image_path),
            "model": model,
            "returncode": None,
            "ok": False,
            "stdout": _collapse_repetition(stdout),
            "stderr": f"ollama review timed out after {timeout}s",
        }
    return {
        "image": str(image_path),
        "model": model,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": _collapse_repetition(proc.stdout.strip()),
        "stderr": proc.stderr.strip(),
    }


def run_glm_ocr(image_path: Path, prompt: str, model: str, timeout: int, *, endpoint: str = "http://127.0.0.1:11434", prefer_api: bool = True) -> dict[str, Any]:
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    if prefer_api:
        result = run_glm_ocr_api(image_path, prompt, model, timeout, endpoint)
        if result["ok"]:
            return result
    return run_glm_ocr_cli(image_path, prompt, model, timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cheap local visual review for OctaneX MCP previews using Ollama glm-ocr.")
    parser.add_argument("--reference", type=Path, required=True, help="target/reference image path")
    parser.add_argument("--candidate", type=Path, required=True, help="native Octane candidate preview path")
    parser.add_argument("--model", default="glm-ocr", help="Ollama model name")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="per-image visual review prompt")
    parser.add_argument("--timeout", type=int, default=45, help="seconds per image")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434", help="Ollama HTTP endpoint")
    parser.add_argument("--cli", action="store_true", help="use `ollama run` instead of the HTTP API")
    args = parser.parse_args()

    reference = run_glm_ocr(args.reference, args.prompt, args.model, args.timeout, endpoint=args.endpoint, prefer_api=not args.cli)
    candidate = run_glm_ocr(args.candidate, args.prompt, args.model, args.timeout, endpoint=args.endpoint, prefer_api=not args.cli)
    print(json.dumps({"ok": reference["ok"] and candidate["ok"], "reference": reference, "candidate": candidate}, indent=2))


if __name__ == "__main__":
    main()
