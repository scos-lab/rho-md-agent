#!/usr/bin/env python3
"""Build the ZIP for the OpenAI plugin directory (ChatGPT / Codex) and check what the portal checks.

    python3 tools/pack_openai.py [plugin-dir]      → dist/rho-md-<version>-openai.zip

The portable manifest plugin.json sits at the ZIP root, skills in skills/, images in assets/
(https://developers.openai.com/plugins/deploy/submission). The Claude Code manifest is left out.
Exits 1 and lists every problem when the package would be rejected.
"""
import json
import pathlib
import re
import struct
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "plugins" / "rho-md"
LEAVE_OUT = {".claude-plugin"}
problems = []


def png_size(path):
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


manifest = json.loads((SRC / "plugin.json").read_text())
ui = manifest.get("extensions", {}).get("com.openai", {}).get("interface", {})

if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", manifest.get("name", "")):
    problems.append("name: lowercase letters, numbers and single hyphens")
for key in ("version", "description"):
    if not manifest.get(key):
        problems.append(f"{key}: missing")
if not manifest.get("author", {}).get("name"):
    problems.append("author.name: missing")
for key, limit in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000)):
    value = ui.get(key, "")
    if not value or len(value) > limit:
        problems.append(f"interface.{key}: {len(value)} characters (1–{limit})")
for key in ("developerName", "category"):
    if not ui.get(key):
        problems.append(f"interface.{key}: missing")
if not isinstance(ui.get("capabilities"), list):
    problems.append("interface.capabilities: must be a list")
if len(ui.get("defaultPrompt", [])) > 3:
    problems.append("interface.defaultPrompt: at most three")
if re.search(r"\$\d|free trial|discount|subscription|pricing", ui.get("longDescription", ""), re.I):
    problems.append("interface.longDescription: no pricing or promotions")
for key in ("logo", "composerIcon"):
    ref = ui.get(key, "")
    path = SRC / ref
    if not ref.startswith("./") or not path.is_file():
        problems.append(f"interface.{key}: {ref!r} is not a ./ path to a file in the package")
        continue
    size = png_size(path)
    if path.stat().st_size > 5 * 1024 * 1024 or not size or size[0] != size[1] or not 48 <= size[0] <= 4096:
        problems.append(f"interface.{key}: square PNG, 48–4096 px, ≤5 MiB (got {size})")

skills = sorted((SRC / "skills").glob("*/SKILL.md"))
if not skills:
    problems.append("skills/: no SKILL.md")
for skill in skills:
    front = re.match(r"---\n(.*?)\n---\n", skill.read_text(), re.S)
    fields = dict(re.findall(r"^(name|description):\s*(.+)$", front.group(1), re.M)) if front else {}
    if not fields.get("name") or not fields.get("description"):
        problems.append(f"{skill.relative_to(SRC)}: YAML header needs name and description")

files = [p for p in sorted(SRC.rglob("*")) if p.is_file() and not (set(p.relative_to(SRC).parts) & LEAVE_OUT)]
for p in files:
    rel = p.relative_to(SRC).as_posix()
    if rel.endswith(".app.json") or rel.startswith("hooks/") or rel in ("hooks.json", "mcp.json", ".mcp.json"):
        problems.append(f"{rel}: hooks, app references and MCP config cannot be in this package")

if problems:
    print("not ready:\n  " + "\n  ".join(problems))
    sys.exit(1)

out = ROOT / "dist" / f"{manifest['name']}-{manifest['version']}-openai.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(SRC).as_posix())
print(f"{out}  ({len(files)} files, {out.stat().st_size // 1024} KiB)")
