#!/usr/bin/env node
// Rho MD client for AI tools. Talks to the Rho MD app on this computer through Agent Connect
// (Settings › AI tools in the app). No dependencies.
//
//   node rho.mjs [--client NAME] <command-id> ['<json args>']
//   node rho.mjs [--client NAME] --status        is Rho MD running, and may this tool use it?
//   node rho.mjs --launch                        start Rho MD and wait until it is ready
//
// Prints the app's reply line. Exit codes: 0 done · 1 the command failed or was declined ·
// 2 Rho MD is not running / not installed / AI tools switched off · 3 this tool is not allowed ·
// 4 usage.

import net from 'node:net';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';

const ID = 'md.rho.app';
const DOWNLOAD = 'https://rho.md/download';
const LABELS = { codex: 'Codex', 'claude-code': 'Claude Code' };

function usage(msg) {
  if (msg) console.error(msg);
  console.error("usage: rho.mjs [--client NAME] <command-id> ['<json args>'] | --status | --launch");
  process.exit(4);
}

/** Where Rho MD keeps agent-connect.json — every install form we ship. */
function candidateDirs() {
  const home = os.homedir();
  const env = process.env;
  const dirs = [];
  if (env.RHO_MD_DATA_DIR) dirs.push(env.RHO_MD_DATA_DIR);
  if (process.platform === 'win32') {
    const local = env.LOCALAPPDATA || path.join(home, 'AppData', 'Local');
    dirs.push(path.join(local, ID));
    // Microsoft Store (MSIX) copies: the package's file system virtualisation keeps the app's
    // LocalAppData writes under Packages\<family>\LocalCache\Local.
    try {
      for (const p of fs.readdirSync(path.join(local, 'Packages'))) {
        dirs.push(path.join(local, 'Packages', p, 'LocalCache', 'Local', ID));
      }
    } catch {}
  } else if (process.platform === 'darwin') {
    dirs.push(path.join(home, 'Library', 'Application Support', ID));
    dirs.push(path.join(home, 'Library', 'Containers', ID, 'Data', 'Library', 'Application Support', ID));
  } else {
    dirs.push(path.join(env.XDG_DATA_HOME || path.join(home, '.local', 'share'), ID));
    dirs.push(path.join(home, 'snap', 'rho-md', 'current', '.local', 'share', ID));
    dirs.push(path.join(home, '.var', 'app', ID, 'data', ID));
  }
  return dirs;
}

/** The newest discovery file, or null. */
function discover() {
  let best = null;
  for (const d of candidateDirs()) {
    const f = path.join(d, 'agent-connect.json');
    try {
      const st = fs.statSync(f);
      if (!best || st.mtimeMs > best.mtime) best = { file: f, mtime: st.mtimeMs };
    } catch {}
  }
  if (!best) return null;
  try {
    const info = JSON.parse(fs.readFileSync(best.file, 'utf8'));
    return typeof info.port === 'number' && typeof info.token === 'string' ? { ...info, file: best.file } : null;
  } catch {
    return null;
  }
}

function guessClient() {
  const env = process.env;
  if (env.CLAUDECODE === '1' || env.CLAUDE_CODE_ENTRYPOINT) return 'claude-code';
  if (Object.keys(env).some((k) => k.startsWith('CODEX_'))) return 'codex';
  return 'ai-tool';
}

const NOT_RUNNING =
  `Rho MD is not running, or "Allow AI tools to use Rho MD" is off in its Settings › AI tools.\n` +
  `Start it with: node "${process.argv[1]}" --launch   (not installed? ${DOWNLOAD})`;

/** One session: hello, then (optionally) one command. Resolves with the reply lines. */
function session(info, client, line, onWait) {
  return new Promise((resolve, reject) => {
    const sock = net.connect({ host: '127.0.0.1', port: info.port });
    let buf = '';
    const replies = [];
    const want = line ? 2 : 1;
    let waitTimer = setTimeout(onWait, 3000);
    sock.setEncoding('utf8');
    sock.on('connect', () => {
      const hello = { token: info.token, client, label: LABELS[client] || client, version: '1' };
      sock.write(`hello ${JSON.stringify(hello)}\n`);
    });
    sock.on('data', (chunk) => {
      buf += chunk;
      let i;
      while ((i = buf.indexOf('\n')) >= 0) {
        const r = buf.slice(0, i).trim();
        buf = buf.slice(i + 1);
        if (!r) continue;
        replies.push(r);
        if (replies.length === 1) {
          if (!r.startsWith('ok')) return finish();
          if (line) {
            clearTimeout(waitTimer);
            waitTimer = setTimeout(onWait, 3000);
            sock.write(line + '\n');
          }
        }
        if (replies.length >= want) return finish();
      }
    });
    sock.on('error', (e) => {
      clearTimeout(waitTimer);
      reject(e);
    });
    sock.on('close', () => finish());
    function finish() {
      clearTimeout(waitTimer);
      sock.destroy();
      resolve(replies);
    }
  });
}

function openUrl(url) {
  const [cmd, args] =
    process.platform === 'win32' ? ['cmd', ['/c', 'start', '', url]] : process.platform === 'darwin' ? ['open', [url]] : ['xdg-open', [url]];
  spawn(cmd, args, { detached: true, stdio: 'ignore' }).unref();
}

async function launch() {
  const before = discover();
  openUrl('rho://');
  for (let i = 0; i < 40; i++) {
    await new Promise((r) => setTimeout(r, 500));
    const now = discover();
    if (now && (!before || now.token !== before.token || now.pid !== before.pid)) {
      console.log(`ok Rho MD ${now.version ?? ''} is ready`);
      return 0;
    }
    if (now && before && i >= 6) {
      // It was already running (the same file): check it answers.
      try {
        const r = await session(now, 'launcher', null, () => {});
        if (r[0]) {
          console.log(`ok Rho MD ${now.version ?? ''} is running`);
          return 0;
        }
      } catch {}
    }
  }
  console.error(`Rho MD did not start within 20 seconds. If it is not installed: ${DOWNLOAD}`);
  return 2;
}

async function main() {
  const argv = process.argv.slice(2);
  let client = null;
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--client') client = argv[++i];
    else rest.push(argv[i]);
  }
  client = (client || guessClient()).toLowerCase();
  if (rest[0] === '--launch') return launch();
  const status = rest[0] === '--status';
  const cmd = status ? null : rest[0];
  if (!status && !cmd) usage();
  if (cmd && cmd.startsWith('-')) usage(`unknown option ${cmd}`);
  let line = null;
  if (cmd) {
    const raw = rest.slice(1).join(' ').trim();
    if (raw) {
      try {
        JSON.parse(raw);
      } catch (e) {
        usage(`the arguments must be JSON: ${e.message}`);
      }
    }
    line = raw ? `${cmd} ${raw}` : cmd;
  }
  const info = discover();
  if (!info) {
    console.error(NOT_RUNNING);
    return 2;
  }
  let replies;
  try {
    replies = await session(info, client, line, () => console.error('… waiting for the person to answer in Rho MD'));
  } catch (e) {
    if (e && (e.code === 'ECONNREFUSED' || e.code === 'ECONNRESET')) {
      console.error(NOT_RUNNING);
      return 2;
    }
    // A sandbox that blocks network sockets shows up here (EPERM / EACCES).
    console.error(`could not reach Rho MD on 127.0.0.1:${info.port}: ${e && e.code ? e.code : e}. If your tool runs commands in a sandbox, allow this command to use the local network.`);
    return 2;
  }
  const hello = replies[0] || '';
  if (!hello.startsWith('ok')) {
    console.log(hello || 'denied {"reason":"the connection closed"}');
    return hello.startsWith('denied') ? 3 : 2;
  }
  if (status) {
    console.log(hello);
    return 0;
  }
  const r = replies[1];
  if (!r) {
    console.error('Rho MD closed the connection before answering');
    return 1;
  }
  console.log(r);
  return r.startsWith('executed') ? 0 : 1;
}

main().then(
  (code) => process.exit(code),
  (e) => {
    console.error(String(e && e.stack ? e.stack : e));
    process.exit(1);
  },
);
