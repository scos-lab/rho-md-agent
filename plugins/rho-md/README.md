# Rho MD

Let your AI tool use [Rho MD](https://rho.md), the Markdown reader and notebook on your computer:
open a Markdown file — or a report it just wrote — so you can read it rendered, with math, diagrams
and interactive charts; read and edit the document you have open; search, tag, move, rename and
index the notes in your Rho MD library; and export to PDF or Word.

## Requirements

- Rho MD 1.4.15 or later, installed and running on the same computer
  ([download](https://download.rho.md/gh)). Rho MD 1.4.15 is available for Windows and Linux; the
  Mac version follows.
- Settings › AI tools › "Allow AI tools to use Rho MD" switched on (the default).

It does not work in cloud sandboxes, where the app is not available.

## What it runs, reads and connects to

- **Runs** one of the bundled client scripts in `skills/rho-md/scripts/`: `rho.mjs` with `node`, or
  `rho.sh` (bash) / `rho.ps1` (PowerShell) where `node` is missing. Each call runs one Rho MD
  command and prints the app's one-line reply. The scripts have no dependencies and download
  nothing.
- **Reads** one file: `agent-connect.json` in Rho MD's own app-data folder, which the app writes
  while it is running (the local port and a key that changes every time Rho MD starts).
- **Connects** only to Rho MD on this computer, at 127.0.0.1 on that port. Nothing is sent over the
  internet.
- **Opens** the `rho://` link when asked to start Rho MD (`--launch`), the same way your system
  opens any app link.
- When Rho MD is not installed, the scripts print a download link (download.rho.md, which leads to
  the download page). They never open or fetch it themselves.

## What it can do, and what it asks first

- Reading and editing run directly.
- Deleting, publishing, sending and uploading always ask you in Rho MD first.
- Account and sign-in actions are not available to AI tools.
- The first AI tool that connects is allowed; any other one asks you first. Rho MD lists every
  tool under Settings › AI tools, where you can remove one or switch the whole thing off, and
  writes each command an AI tool runs to its log file on your device.

Privacy policy: https://rho.md/legal/privacy (§5c).

## Support

support@rho.md

## License

MIT
