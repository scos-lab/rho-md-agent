# Rho MD for Codex and Claude Code

Let your AI coding tool use [Rho MD](https://rho.md), the Markdown reader and notebook on your
computer: open a Markdown file — or a report it just wrote — so you can read it rendered, read and
edit the document you have open, search, tag, move and index the notes in your Rho MD library, and
export to PDF or Word.

## Requirements

- Rho MD 1.4.15 or later, installed and running on the same computer ([download](https://download.rho.md/gh)).
  Rho MD 1.4.15 is available for Windows and Linux; the Mac version follows.
- Settings › AI tools › "Allow AI tools to use Rho MD" switched on (the default).

The plugin does not work in cloud sandboxes, where the app is not available.

## Install

**Codex**

```
codex plugin marketplace add scos-lab/rho-md-agent
codex plugin add rho-md@rho-md
```

**Claude Code**

```
/plugin marketplace add scos-lab/rho-md-agent
/plugin install rho-md@rho-md
```

Then ask, for example: "Open the report you just wrote in Rho MD".

## What it can do, and what it asks first

The plugin's skill runs Rho MD commands through a small client script (`node`, with `bash` and
PowerShell fallbacks) that talks to the app over a local connection on 127.0.0.1. Nothing goes
over the internet.

- Reading and editing run directly.
- Deleting, publishing, sending and uploading always ask you in Rho MD first.
- Account and sign-in actions are not available to AI tools.
- The first AI tool that connects is allowed; any other one asks you first. Rho MD lists every tool
  under Settings › AI tools, where you can remove one or switch the whole thing off.

## Layout

```
.agents/plugins/marketplace.json     Codex marketplace
.claude-plugin/marketplace.json      Claude Code marketplace
plugins/rho-md/
  plugin.json                        portable manifest (+ Codex listing details)
  .claude-plugin/plugin.json         Claude Code manifest
  skills/rho-md/SKILL.md             the skill
  skills/rho-md/scripts/             rho.mjs · rho.sh · rho.ps1
  skills/rho-md/references/          command reference
tools/pack_openai.py                 builds and checks the ZIP for the OpenAI plugin directory
```

## Support

support@rho.md

## License

MIT
