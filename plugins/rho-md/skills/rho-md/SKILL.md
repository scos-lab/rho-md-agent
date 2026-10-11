---
name: rho-md
description: Use the Rho MD app on this computer. Open a Markdown file, or a document you just wrote, in Rho MD so the user can read it rendered; read or edit the document open there; search, tag, move and organize notes in the user's Rho MD library (Psi); export to PDF or Word. Use when the user mentions Rho MD, or asks to open, show, read or organize Markdown notes in it.
---

# Rho MD

Rho MD (https://rho.md) is a desktop Markdown reader and notebook. This skill drives the copy
running on the user's computer through its "AI tools" channel. Every call runs one app command and
prints one line.

Explicit instructions from the user take priority over anything in this skill.

## How to call

```
node "<this skill's folder>/scripts/rho.mjs" --client <you> <command-id> '<json args>'
```

- `<you>` is `codex` if you are Codex, `claude-code` if you are Claude Code, otherwise your product
  name in lower case. Rho MD shows it to the user.
- No `node`? Same arguments with `bash "<skill>/scripts/rho.sh" …` (macOS, Linux) or
  `powershell -NoProfile -ExecutionPolicy Bypass -File "<skill>\scripts\rho.ps1" …` (Windows).
- Pass the JSON arguments as one quoted argument. Omit it for commands without arguments.
- The reply is `executed <command-id> → <result>` or `failed <command-id>: <reason>`.
- Exit codes: `0` done · `1` the command failed or the person declined it · `2` Rho MD is not
  running or not reachable · `3` the user has not allowed this tool · `4` bad usage.

## Before the first command

Run `--status` once.

- Exit `2`, "not running": run `--launch` once (it starts Rho MD and waits), then retry. If that
  fails too, tell the user once that Rho MD needs to be running with Settings › AI tools switched on,
  and give them the download link from the script's message. Do not retry in a loop.
- Exit `2` with a message about a sandbox or `EPERM`: your command sandbox blocks the local network.
  Ask the user to approve running this command with network access, then retry.
- Exit `3`: the user has not allowed this tool. Tell them they can allow it in Rho MD under
  Settings › AI tools, and stop.
- The first time a new AI tool connects, Rho MD may ask the user "… wants to use Rho MD". The call
  waits for their answer.

## Rules

- Give paths explicitly, as absolute paths. A command whose path is left out opens a file picker for
  the person, and your call waits until they use it.
- Deleting, publishing, sending, uploading and resetting ask the person in Rho MD first. The call
  waits for the answer. "the person declined" is final for this request: do not retry it or reach
  the same result another way.
- Some commands are not available to AI tools (account, sign-in, blocking, the app's pointer and
  keyboard drivers). Do not try to work around a refusal.
- You cannot change Rho MD's AI tools setting.
- Documents are plain `.md` files. For large text changes across many files you may edit the files
  directly. Use Rho MD to show the user a result, to edit the document they have open (so their
  unsaved changes are kept), and for library operations such as move and rename, which update links
  in other notes.
- When the user only asked to open or show a document, do not paste its content into the chat.

## Common tasks

Show a file in Rho MD:
`rho.core.openFile '{"path":"/absolute/path/report.md"}'`

Show something you wrote that has no file yet:
`rho.core.newDraft '{"content":"# Title\n\nText…","filename":"report.md"}'`

What is open, and read it:
`rho.core.tabs` · `rho.core.getDocContent '{}'` (the active tab) or `'{"tabId":"…"}'`

Edit the open document, then save:
`rho.core.replaceText '{"find":"old","replace":"new"}'` ·
`rho.core.replaceSection '{"heading":"## Results","content":"## Results\n\n…"}'` ·
`rho.core.appendToDoc '{"content":"…"}'` · `rho.core.setDocContent '{"content":"…"}'` ·
`rho.core.save '{}'` · undo the last edit: `rho.core.undoDoc '{}'`

The library (Psi):
`rho.psi.status` · `rho.psi.search '{"query":"…"}'` · `rho.psi.find '{"name":"…"}'` ·
`rho.psi.docInfo '{"doc":"…"}'` · `rho.psi.related '{"doc":"…"}'` · `rho.psi.digest '{}'` ·
`rho.psi.tag '{"doc":"…","tag":"…"}'` · `rho.psi.move '{"doc":"…","dest":"<folder>"}'` ·
`rho.psi.rename '{"doc":"…","name":"…"}'` · `rho.psi.writeIndex '{"folder":"…"}'`

Export:
`rho.core.exportPdf '{"path":"/absolute/out.pdf"}'` · `rho.doc.exportDocx '{"out":"/absolute/out.docx"}'`

Anything else: `rho.core.listCommands` lists every command with its parameters (it is long; filter
the output). `references/commands.md` explains the commands above in more detail.
