# Rho MD commands for AI tools

Parameters are one JSON object. `?` marks an optional key. "Asks" means Rho MD asks the person
before it runs. Run `rho.core.listCommands` for the full, current list.

## Documents and tabs

| Command | Parameters | Notes |
|---|---|---|
| `rho.core.tabs` | — | Open tabs, the active one, edit state. |
| `rho.core.openFile` | `{path}` | Opens a Markdown file in a tab. Always pass `path`; without it a file picker opens for the person. |
| `rho.core.newDraft` | `{content, filename?}` | A new unsaved tab with this content. Closing it discards it. |
| `rho.core.getDocContent` | `{tabId?}` | `{name, path, dirty, content}` of the active tab, or of `tabId`. |
| `rho.core.setDocContent` | `{content, tabId?}` | Replaces the whole document text. |
| `rho.core.replaceText` | `{find, replace, all?, tabId?}` | `find` is exact text and may span lines; `all: "true"` replaces every occurrence. |
| `rho.core.replaceSection` | `{heading, content, tabId?}` | `content` replaces the whole section, its heading line included. |
| `rho.core.appendToDoc` | `{content, tabId?}` | Appends at the end. |
| `rho.core.undoDoc` | `{tabId?}` | Undoes the last edit. |
| `rho.core.save` | `{}` | Saves the active document. |
| `rho.core.find` | `{query}` | Opens find in the document and jumps to the first match. |

## The library (Psi)

Psi is the user's local notes library: ordinary folders of `.md` files that Rho MD indexes.
`doc` and `folder` accept a name as the user said it, a relative path inside the library, or an
absolute path.

| Command | Parameters | Notes |
|---|---|---|
| `rho.psi.status` | — | Whether a library is set up, and its state. |
| `rho.psi.digest` | `{days?}` | Library numbers: notes, folders, recently changed (default 7 days). |
| `rho.psi.search` | `{query}` | Notes whose name or text match any of the words; notes with all of them rank first. |
| `rho.psi.find` | `{name}` | Resolves a folder or note name (or a tail like `Sub/note.md`) to its path. |
| `rho.psi.docInfo` | `{doc}` | What the library knows about one note. |
| `rho.psi.related` | `{doc, limit?}` | Notes related to this one. |
| `rho.psi.tag` | `{doc, tag}` | Adds a tag. |
| `rho.psi.move` | `{doc, dest}` | Moves a note into folder `dest`; links in other notes are updated. |
| `rho.psi.rename` | `{doc, name}` | Renames a note; links are updated. |
| `rho.psi.writeIndex` | `{folder, oneLiners?}` | Writes the folder's `index.md` table of contents (never overwrites a hand-written one). |
| `rho.psi.archive` | `{doc}` | Moves a note (or a whole folder) to the Trash. Asks. |

## Export

| Command | Parameters | Notes |
|---|---|---|
| `rho.core.exportPdf` | `{path, tabId?}` | Writes a PDF of the document. |
| `rho.doc.exportDocx` | `{path?, out?}` | Writes a Word file of `path` (default: the open document) to `out`. |

## Rendered extras

Rho MD renders standard Markdown plus math, Mermaid diagrams, and interactive blocks (charts,
sliders, quizzes). Plain Markdown always works.
