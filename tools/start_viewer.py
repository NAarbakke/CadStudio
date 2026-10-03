"""Start/reuse this project's CAD Viewer and verify saved exports over HTTP."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import parse_qs, quote, urlencode, urlsplit
from urllib.request import Request, urlopen
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"


def request(url, *, post=False, binary=False):
    req = Request(url, data=b"" if post else None)
    with urlopen(req, timeout=60) as response:
        data = response.read()
    return data if binary else json.loads(data)


def start(port=None):
    command = [sys.executable, "-m", "cadgen.cli", "viewer",
               "--host", "127.0.0.1", "--json", "--detach"]
    if port is not None:
        command.extend(["--port", str(port)])
    result = subprocess.run(command, cwd=MODELS, capture_output=True, text=True,
                            timeout=150)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr, flush=True)
    announcements = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and "url" in item:
            announcements.append(item)
    if not announcements:
        raise RuntimeError("Viewer returned no URL: " + result.stdout)
    url = announcements[-1]["url"].rstrip("/")
    info = request(url + "/__cad/server")
    if Path(info["rootPath"]).resolve() != MODELS.resolve():
        raise RuntimeError(f"Viewer serves {info['rootPath']}, expected {MODELS}")
    return url, info


def store_url(url, ref, asset):
    params = parse_qs(urlsplit(ref).query)
    tree = params["file"][0].rstrip("/")
    query = {key: values[0] for key, values in params.items()}
    query["file"] = tree + "/" + asset
    return url + "/__cad/store?" + urlencode(query)


def check_step(url, relative, timeout):
    endpoint = url + "/__cad/artifact?" + urlencode({"file": relative})
    status = request(endpoint)
    if status["state"] == "not-compiled" and status.get("compile"):
        print(f"Compiling viewer cache: {relative}", flush=True)
        request(endpoint, post=True)
        status = request(endpoint)
    deadline = time.monotonic() + timeout
    while status["state"] in ("compiling", "building"):
        if time.monotonic() > deadline:
            raise RuntimeError(f"Viewer cache still compiling after {timeout}s")
        time.sleep(1)
        status = request(endpoint)
    if status["state"] != "compiled" or not status.get("ref"):
        raise RuntimeError(json.dumps(status))
    assembly = request(store_url(url, status["ref"], "assembly.json"))
    components = assembly.get("components", {})
    if not components:
        raise RuntimeError("Assembly has no components")
    for component in components.values():
        asset = component.get("brep") or component.get("mesh")
        if asset and not request(store_url(url, status["ref"], asset), binary=True):
            raise RuntimeError(f"Empty component asset: {asset}")
    leaves = assembly["assembly"]["root"]["leafPartIds"]
    return len(leaves) if isinstance(leaves, list) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", help="Source stem, e.g. turbofan")
    parser.add_argument("--format", choices=("STEP", "GLB", "STL"), default="STEP")
    parser.add_argument("--open", action="store_true", help="Open the system browser")
    parser.add_argument("--check-all", action="store_true", help="Check all saved STEP/STL/GLB exports")
    parser.add_argument("--port", type=int, help="Require this port; otherwise reuse/choose a free port")
    parser.add_argument("--compile-timeout", type=int, default=1200)
    args = parser.parse_args()
    sources = sorted((MODELS / "src").glob("*.py"))
    stems = {path.stem for path in sources}
    if args.model is not None and args.model not in stems:
        parser.error("Unknown model. Choose: " + ", ".join(sorted(stems)))
    relative = None
    if args.model:
        relative = f"{args.format}/{args.model}.{args.format.lower()}"
        if not (MODELS / relative).is_file():
            parser.error(f"Missing {relative}. Build models/src/{args.model}.py first.")
    url, info = start(args.port)
    print(f"CAD Viewer {info['viewerVersion']}: {url}/", flush=True)
    print(f"Serving: {info['rootPath']}", flush=True)
    failures = []
    checks = {}
    if args.check_all:
        for stem in sorted(stems):
            for fmt in ("STEP", "GLB", "STL"):
                ref = f"{fmt}/{stem}.{fmt.lower()}"
                try:
                    if not (MODELS / ref).is_file():
                        raise RuntimeError("Export missing; run the model source first")
                    if fmt == "STEP":
                        count = check_step(url, ref, args.compile_timeout)
                        checks[ref] = {"ok": True, "parts": count}
                        print(f"OK {ref}: {count} parts, assembly and component assets readable", flush=True)
                    else:
                        # The viewer asset route requires an absolute contained
                        # file; artifact status accepts root-relative paths.
                        data = request(url + "/__cad/asset?" + urlencode({"file": str(MODELS / ref)}), binary=True)
                        if not data:
                            raise RuntimeError("Export is empty")
                        checks[ref] = {"ok": True, "bytes": len(data)}
                        print(f"OK {ref}: {len(data):,} bytes", flush=True)
                except Exception as exc:
                    failures.append(ref)
                    checks[ref] = {"ok": False, "error": str(exc)}
                    print(f"FAILED {ref}: {exc}", flush=True)
    target = url + "/" + ("?file=" + quote(relative, safe="") if relative else "")
    state = {"checked_at": datetime.now(timezone.utc).isoformat(),
             "url": target, "server": info, "checks": checks,
             "model_urls": {stem: url + "/?file=" + quote(f"STEP/{stem}.step", safe="")
                            for stem in sorted(stems)}}
    state_path = ROOT / "tmp" / "viewer" / "session.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"Open: {target}", flush=True)
    print(f"Session and check results: {state_path}", flush=True)
    if args.open:
        webbrowser.open(target)
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Viewer error: {exc}", file=sys.stderr)
        raise SystemExit(1)
