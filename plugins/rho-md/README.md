# Rho MD

Two things in one plugin:

- **Search Rho Cloud.** Search the documents people publish on [rho.md](https://rho.md) — books,
  notes, guides and research, in English, Chinese and other languages — and read any of them in
  full, with a link to the source. Works wherever the plugin's tools run, including claude.ai.
- **Use the Rho MD app on your computer** (Claude Code on your own machine): open a Markdown file —
  or a report it just wrote — so you can read it rendered, with math, diagrams and interactive
  charts; read and edit the document you have open; search, tag, move, rename and index the notes
  in your Rho MD library; and export to PDF or Word.

## Requirements

- Searching Rho Cloud needs nothing installed.
- Using the app needs Rho MD 1.4.15 or later, installed and running on the same computer
  ([download](https://download.rho.md/cc)), with Settings › AI tools › "Allow AI tools to use
  Rho MD" switched on (the default). Rho MD 1.4.15 is available for Windows and Linux; the Mac
  version follows. This part does not work in cloud sandboxes, where the app is not available.

## Install

- **Claude Code:** `/plugin install rho-md --marketplace scos-lab/rho-md-agent`
- **Codex:** `codex plugin marketplace add scos-lab/rho-md-agent`, then `codex plugin add rho-md@rho-md`

## What it runs, reads and connects to

- **Rho Cloud search** connects to `https://rho.md/api/mcp` (an MCP server run by Rho MD). It sends
  the search words, or the id of the document asked for, and gets back published documents only —
  never private or unlisted ones. Searches are not logged; see the privacy policy, §5d.
- **The app part runs** one of the bundled client scripts in `skills/rho-md/scripts/`: `rho.mjs`
  with `node`, or `rho.sh` (bash) / `rho.ps1` (PowerShell) where `node` is missing. Each call runs
  one Rho MD command and prints the app's one-line reply. The scripts have no dependencies and
  download nothing.
- It **reads** one file: `agent-connect.json` in Rho MD's own app-data folder, which the app writes
  while it is running (the local port and a key that changes every time Rho MD starts).
- The app part **connects** only to Rho MD on this computer, at 127.0.0.1 on that port; nothing
  from your library is sent over the internet.
- It **opens** the `rho://` link when asked to start Rho MD (`--launch`), the same way your system
  opens any app link.
- The scripts contain no web addresses at all. When Rho MD is not installed, the skill has the AI
  give you a download link (download.rho.md, which leads to the download page).

## What it can do, and what it asks first

- Searching and reading Rho Cloud are read-only.
- In the app, reading and editing run directly; deleting, publishing, sending and uploading always
  ask you in Rho MD first; account and sign-in actions are not available to AI tools.
- The first AI tool that connects to the app is allowed; any other one asks you first. Rho MD lists
  every tool under Settings › AI tools, where you can remove one or switch the whole thing off, and
  writes each command an AI tool runs to its log file on your device.

Privacy policy: https://rho.md/legal/privacy (§5c for the app, §5d for Rho Cloud search).

## Support

support@rho.md · https://rho.md/feedback

## License

MIT
