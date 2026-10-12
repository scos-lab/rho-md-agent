#!/usr/bin/env python3
"""Build the ZIP for the OpenAI plugin directory (ChatGPT / Codex) and check what the portal checks.

    python3 tools/pack_openai.py [plugin-dir]      → dist/rho-md-<version>-openai.zip

The portable manifest plugin.json sits at the ZIP root, skills in skills/, images in assets/
(https://developers.openai.com/plugins/deploy/submission). The Claude Code manifest is left out.
Exits 1 and lists every problem when the package would be rejected. With an mcp.json the package
is a "With MCP" submission: the server must be a remote streamable-http HTTPS URL, and review needs
exactly 5 positive and 3 negative test cases and the four listing URLs (a missing demo recording is
only a warning, so a draft can be uploaded and scanned before the video exists).
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
for key in ("developerName", "category", "supportURL", "privacyPolicyURL"):
    if not ui.get(key):
        problems.append(f"interface.{key}: missing")
for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
    if ui.get(key) and not ui[key].startswith("https://"):
        problems.append(f"interface.{key}: must be an https:// URL")
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

warnings = []
for agent in sorted((SRC / "skills").glob("*/agents/openai.yaml")):
    text = agent.read_text()
    rel = agent.relative_to(SRC)
    if not re.search(r"^interface:\s*$", text, re.M) or not re.search(r"^\s+display_name:\s*\S", text, re.M) \
            or not re.search(r"^\s+short_description:\s*\S", text, re.M):
        problems.append(f"{rel}: interface needs display_name and short_description")
    for prod in re.findall(r"^\s+-\s*(\S+)\s*$", text, re.M):
        if prod not in ("CHAT", "CODEX"):
            problems.append(f"{rel}: policy.products may only list CHAT and CODEX (got {prod})")

mcp_path = SRC / "mcp.json"
if mcp_path.is_file():
    servers = json.loads(mcp_path.read_text()).get("mcpServers", {})
    if len(servers) != 1:
        problems.append(f"mcp.json: exactly one MCP server per plugin (got {len(servers)})")
    for name, srv in servers.items():
        if srv.get("type") != "streamable-http" or not str(srv.get("url", "")).startswith("https://"):
            problems.append(f"mcp.json: {name} must be a remote streamable-http server on an https:// URL")
        auth = srv.get("extensions", {}).get("com.openai", {}).get("auth", {}).get("type")
        if auth not in ("none", "oauth", "mixed"):
            problems.append(f"mcp.json: {name} needs extensions.com.openai.auth.type none, oauth or mixed (got {auth!r})")
        if srv.get("headers"):
            problems.append(f"mcp.json: {name}: public submission rejects server headers")
    review = manifest.get("extensions", {}).get("com.openai", {}).get("review", {})
    cases = review.get("test_cases", {})
    pos, neg = cases.get("positive", []), cases.get("negative", [])
    if len(pos) != 5 or len(neg) != 3:
        problems.append(f"review.test_cases: exactly 5 positive and 3 negative (got {len(pos)} and {len(neg)})")
    for i, c in enumerate(pos):
        missing = [k for k in ("description", "prompt", "tools_triggered", "expected_behavior") if not c.get(k)]
        if missing:
            problems.append(f"review.test_cases.positive[{i}]: missing {', '.join(missing)}")
    for i, c in enumerate(neg):
        missing = [k for k in ("description", "prompt") if not c.get(k)]
        if missing:
            problems.append(f"review.test_cases.negative[{i}]: missing {', '.join(missing)}")
    for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        if not ui.get(key):
            problems.append(f"interface.{key}: required for MCP review")
    if not review.get("demo_recording_url"):
        warnings.append("review.demo_recording_url: needed before Submit for review")
    if not manifest.get("extensions", {}).get("com.openai", {}).get("publication", {}).get("release_notes"):
        problems.append("publication.release_notes: required")
    if ui.get("screenshots"):
        problems.append("interface.screenshots: only for MCP servers with custom UI")

files = [p for p in sorted(SRC.rglob("*")) if p.is_file() and not (set(p.relative_to(SRC).parts) & LEAVE_OUT)]
for p in files:
    rel = p.relative_to(SRC).as_posix()
    if rel.endswith(".app.json") or rel.startswith("hooks/") or rel in ("hooks.json", ".mcp.json"):
        problems.append(f"{rel}: hooks, app references and Codex-format MCP config cannot be in this package")

if problems:
    print("not ready:\n  " + "\n  ".join(problems))
    sys.exit(1)

out = ROOT / "dist" / f"{manifest['name']}-{manifest['version']}-openai.zip"
out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(SRC).as_posix())
print(f"{out}  ({len(files)} files, {out.stat().st_size // 1024} KiB)")
for w in warnings:
    print(f"warning: {w}")
