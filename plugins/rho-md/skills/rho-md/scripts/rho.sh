#!/usr/bin/env bash
# Rho MD client without node (macOS, Linux). Same arguments and exit codes as rho.mjs:
#   bash rho.sh [--client NAME] <command-id> ['<json args>'] | --status | --launch
# Exit: 0 done · 1 failed/declined · 2 not running · 3 not allowed · 4 usage.
set -u
ID=md.rho.app
client=""
rest=()
while [ $# -gt 0 ]; do
  case "$1" in
    --client) client="${2:-}"; shift 2 ;;
    *) rest+=("$1"); shift ;;
  esac
done
if [ -z "$client" ]; then
  if [ "${CLAUDECODE:-}" = 1 ]; then client=claude-code
  elif env | grep -q '^CODEX_'; then client=codex
  else client=ai-tool; fi
fi
client=$(printf '%s' "$client" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9-' '-' | sed 's/^-*//; s/-*$//')
case "$client" in codex) label=Codex ;; claude-code) label="Claude Code" ;; *) label=$client ;; esac

discover() {
  local dirs=() f newest=""
  [ -n "${RHO_MD_DATA_DIR:-}" ] && dirs+=("$RHO_MD_DATA_DIR")
  if [ "$(uname)" = Darwin ]; then
    dirs+=("$HOME/Library/Application Support/$ID" "$HOME/Library/Containers/$ID/Data/Library/Application Support/$ID")
  else
    dirs+=("${XDG_DATA_HOME:-$HOME/.local/share}/$ID" "$HOME/snap/rho-md/current/.local/share/$ID" "$HOME/.var/app/$ID/data/$ID")
  fi
  for d in "${dirs[@]}"; do
    f="$d/agent-connect.json"
    [ -f "$f" ] || continue
    if [ -z "$newest" ] || [ "$f" -nt "$newest" ]; then newest="$f"; fi
  done
  [ -n "$newest" ] || return 1
  json=$(cat "$newest")
  port=$(printf '%s' "$json" | sed -n 's/.*"port":\([0-9][0-9]*\).*/\1/p')
  token=$(printf '%s' "$json" | sed -n 's/.*"token":"\([0-9a-f]*\)".*/\1/p')
  [ -n "$port" ] && [ -n "$token" ]
}

not_running() {
  echo "Rho MD is not running, or \"Allow AI tools to use Rho MD\" is off in its Settings › AI tools." >&2
  echo "Start it with: bash \"$0\" --launch. If Rho MD is not installed, it has to be installed first (the skill gives the link)." >&2
  exit 2
}

if [ "${rest[0]:-}" = --launch ]; then
  discover && before="$token" || before=""
  if [ "$(uname)" = Darwin ]; then open 'rho://' >/dev/null 2>&1 & else xdg-open 'rho://' >/dev/null 2>&1 & fi
  for _ in $(seq 1 40); do
    sleep 0.5
    if discover && [ "$token" != "$before" ]; then echo "ok Rho MD is ready"; exit 0; fi
    if [ -n "$before" ] && discover && (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then echo "ok Rho MD is running"; exit 0; fi
  done
  echo "Rho MD did not start within 20 seconds. If Rho MD is not installed, it has to be installed first (the skill gives the link)." >&2
  exit 2
fi

status=0
[ "${rest[0]:-}" = --status ] && status=1
cmd="${rest[0]:-}"
[ -n "$cmd" ] || { echo "usage: rho.sh [--client NAME] <command-id> ['<json args>'] | --status | --launch" >&2; exit 4; }
line="$cmd"
[ "$status" = 0 ] && [ ${#rest[@]} -gt 1 ] && line="$cmd ${rest[*]:1}"

discover || not_running
exec 3<>"/dev/tcp/127.0.0.1/$port" 2>/dev/null || not_running
printf 'hello {"token":"%s","client":"%s","label":"%s"}\n' "$token" "$client" "$label" >&3
IFS= read -r hello <&3 || not_running
case "$hello" in
  ok*) ;;
  denied*) echo "$hello"; exit 3 ;;
  *) not_running ;;
esac
if [ "$status" = 1 ]; then echo "$hello"; exit 0; fi
printf '%s\n' "$line" >&3
IFS= read -r reply <&3 || { echo "Rho MD closed the connection before answering" >&2; exit 1; }
echo "$reply"
case "$reply" in executed*) exit 0 ;; *) exit 1 ;; esac
