"""Preserve CadStudio's hidden Windows workers after reinstalling cadgen.

Run with the project interpreter after pip install. Only the four known worker
launch sites in cadgen 0.7.10 are patched; already-patched sites are unchanged.
"""
import ast
from importlib import metadata, util
from pathlib import Path
import sys


def patched_source(source):
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = []
    calls = [node for node in ast.walk(ast.parse(source))
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and isinstance(node.func.value, ast.Name)
             and node.func.value.id == "subprocess" and node.func.attr == "Popen"]
    if len(calls) != 1:
        raise RuntimeError(f"Expected one worker launch, found {len(calls)}")
    for call in calls:
        if any(k.arg == "creationflags" for k in call.keywords):
            continue
        # AST columns are byte offsets; preserve non-ASCII source comments.
        line = lines[call.end_lineno - 1]
        column = len(line.encode("utf-8")[:call.end_col_offset - 1].decode("utf-8"))
        position = offsets[call.end_lineno - 1] + column
        if source[position] != ")":
            raise RuntimeError("Unexpected worker launch syntax")
        separator = " " if source[:position].rstrip().endswith(",") else ", "
        edits.append((position, separator + 'creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)'))
    for position, addition in sorted(edits, reverse=True):
        source = source[:position] + addition + source[position:]
    ast.parse(source)
    return source


def main():
    if sys.platform != "win32":
        print("No Windows worker patch needed on this platform.")
        return
    version = metadata.version("cadgen")
    if version != "0.7.10":
        raise SystemExit(f"Review worker launch sites before patching cadgen {version}.")
    package = Path(util.find_spec("cadgen").origin).parent
    # Validate every site before changing any of them.
    updates = []
    for name in ("pool", "executors", "artifacts", "housekeeping"):
        path = package / "daemon" / f"{name}.py"
        original = path.read_text(encoding="utf-8")
        updates.append((path, original, patched_source(original)))
    for path, original, updated in updates:
        if updated != original:
            path.write_text(updated, encoding="utf-8")
        print(f"{path.name}: {'patched' if updated != original else 'already patched'}")


if __name__ == "__main__":
    main()
