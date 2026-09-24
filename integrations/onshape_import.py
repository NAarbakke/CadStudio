"""Upload STEP files to Onshape and translate them into Part Studios / Assemblies.

    set ONSHAPE_ACCESS_KEY=...   (create a key pair at https://dev-portal.onshape.com/keys)
    set ONSHAPE_SECRET_KEY=...
    .venv\\Scripts\\python integrations\\onshape_import.py models\\STEP\\turbofan.step [more.step ...]

Creates a new document named "CadStudio" unless --document <id> is given (the id is the
long hex string after /documents/ in the Onshape URL). Each run adds new tabs; it does not
replace earlier imports.
"""
import argparse
import os
import pathlib
import time

import requests

BASE = "https://cad.onshape.com/api/v6"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("steps", nargs="+", type=pathlib.Path)
    ap.add_argument("--document", help="existing document id to import into")
    ap.add_argument("--name", default="CadStudio", help="name for a new document")
    ap.add_argument("--flatten", action="store_true", help="import assemblies as one Part Studio")
    args = ap.parse_args()

    try:
        auth = (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
    except KeyError:
        raise SystemExit("Set ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY (https://dev-portal.onshape.com/keys)")
    s = requests.Session()
    s.auth = auth
    s.headers["Accept"] = "application/json"

    if args.document:
        doc = s.get(f"{BASE}/documents/{args.document}")
    else:
        doc = s.post(f"{BASE}/documents", json={"name": args.name})
    doc.raise_for_status()
    did, wid = doc.json()["id"], doc.json()["defaultWorkspace"]["id"]

    for step in args.steps:
        with open(step, "rb") as f:
            r = s.post(f"{BASE}/translations/d/{did}/w/{wid}",
                       files={"file": (step.name, f)},
                       data={"translate": "true", "storeInDocument": "false",
                             "flattenAssemblies": str(args.flatten).lower()})
        r.raise_for_status()
        tid = r.json()["id"]
        while (state := s.get(f"{BASE}/translations/{tid}").json())["requestState"] == "ACTIVE":
            time.sleep(3)
        if state["requestState"] != "DONE":
            raise SystemExit(f"{step.name}: translation failed: {state.get('failureReason')}")
        print(f"imported {step.name}")

    print(f"https://cad.onshape.com/documents/{did}/w/{wid}")


if __name__ == "__main__":
    main()
