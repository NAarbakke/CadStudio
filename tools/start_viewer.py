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
    # The viewer refuses a POST without its guard header (cross-site POST block).
    req = Request(url, data=b"" if post else None,
                  headers={"x-cadgen-viewer": "1"} if post else {})
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
    # A reused viewer keeps the folder it was started in; relative ?file= links
    # resolve against it, so it has to be this project's models/.
    if Path(info["start"]).resolve() != MODELS.resolve():
        raise RuntimeError(f"Viewer was started in {info['start']}, expected {MODELS}")
    return url, info


def store_url(url, ref, asset):
    params = parse_qs(urlsplit(ref).query)
    tree = params["file"][0].rstrip("/")
    query = {key: values[0] for key, values in params.items()}
    query["file"] = tree + "/" + asset
    return url + "/__cad/store?" + urlencode(query)


def check_step(url, relative, timeout):
    # The viewer takes absolute paths only.
    file = (MODELS / relative).as_posix()
    endpoint = url + "/__cad/artifact?" + urlencode({"file": file})
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
    if status["state"] != "compiled":
        raise RuntimeError(json.dumps(status))
    # The compiled tree is named by the file's catalog row.
    entries = request(url + "/__cad/catalog?" + urlencode({"file": file}))["entries"]
    if not entries or not entries[0].get("url"):
        raise RuntimeError("Compiled, but the viewer catalog has no entry for it")
    ref = entries[0]["url"]
    assembly = request(store_url(url, ref, "assembly.json"))
    components = assembly.get("components", {})
    if not components:
        raise RuntimeError("Assembly has no components")
    for component in components.values():
        asset = component.get("brep") or component.get("mesh")
        if asset and not request(store_url(url, ref, asset), binary=True):
            raise RuntimeError(f"Empty component asset: {asset}")
    leaves = assembly["assembly"]["root"]["leafPartIds"]
    return len(leaves) if isinstance(leaves, list) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", help="Source stem, e.g. ge_e3_turbofan")
    parser.add_argument("--format", choices=("STEP", "GLB", "STL"), default="STEP")
    parser.add_argument("--open", action="store_true", help="Open the system browser")
    parser.add_argument("--check-all", action="store_true", help="Check all saved STEP/STL/GLB exports")
    parser.add_argument("--port", type=int, help="Require this port; otherwise reuse/choose a free port")
    parser.add_argument("--compile-timeout", type=int, default=1200)
    args = parser.parse_args()
    # A model is a folder models/<stem>/ whose src/ holds <stem>.py.
    stems = {path.parent.parent.name for path in MODELS.glob("*/src/*.py")
             if path.stem == path.parent.parent.name}
    if args.model is not None and args.model not in stems:
        parser.error("Unknown model. Choose: " + ", ".join(sorted(stems)))
    relative = None
    if args.model:
        relative = f"{args.model}/{args.format}/{args.model}.{args.format.lower()}"
        if not (MODELS / relative).is_file():
            parser.error(f"Missing {relative}. Build models/{args.model}/src/{args.model}.py first.")
    url, info = start(args.port)
    print(f"CAD Viewer {info['identityToken'].split(':')[0]}: {url}/", flush=True)
    print(f"Started in: {info['start']}", flush=True)
    failures = []
    checks = {}
    if args.check_all:
        for stem in sorted(stems):
            if not any((MODELS / stem / fmt).is_dir() for fmt in ("STEP", "GLB", "STL")):
                print(f"SKIPPED {stem}: never built", flush=True)
                continue
            for fmt in ("STEP", "GLB", "STL"):
                ref = f"{stem}/{fmt}/{stem}.{fmt.lower()}"
                try:
                    if not (MODELS / ref).is_file():
                        raise RuntimeError("Export missing; run the model source first")
                    if fmt == "STEP":
                        count = check_step(url, ref, args.compile_timeout)
                        checks[ref] = {"ok": True, "parts": count}
                        print(f"OK {ref}: {count} parts, assembly and component assets readable", flush=True)
                    else:
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
             "model_urls": {stem: url + "/?file=" + quote(f"{stem}/STEP/{stem}.step", safe="")
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
