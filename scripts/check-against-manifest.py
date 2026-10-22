#!/usr/bin/env python3
"""Fail when a docs page contradicts Heimdall's feature manifest.

The manifest (`docs/generated/heimdall-features.json` in the bot repo) is generated from the
source and is the authority on what commands and permission keys exist. Until now nothing
compared the prose against it, so this repo could be confidently wrong about something the bot
had renamed - and a wrong permission key is the worst kind, because Heimdall resolves an unknown
key to *denied* and logs at info. A role assigned one looks configured and silently does nothing.

Four checks:

  1. Every permission-key-shaped string in a page exists in the manifest.
  2. Every slash command mentioned exists in the manifest.
  3. Every plugin declaring a docsPath has a page at that path.
  4. Every dashboard deep link (`<DashboardLink to="...">`, or a raw `bot.bifrost.gg/go/...`
     URL) names a key in Heimdall's `docs/generated/dashboard-links.json`, and every page using
     the component imports it. Skipped only when that file is not passed.

Deliberately conservative about what it treats as a claim. A false positive here trains people
to ignore the check, which is worse than not having it, so it only inspects strings inside
backticks and skips anything that looks like an example placeholder.

Run from the docs repo root:
    python3 scripts/check-against-manifest.py path/to/heimdall-features.json [path/to/dashboard-links.json]
"""
import json
import os
import re
import sys

MANIFEST = sys.argv[1] if len(sys.argv) > 1 else "heimdall-features.json"
DASHBOARD_LINKS = sys.argv[2] if len(sys.argv) > 2 else None

# Dashboard deep links. The component's `to` must be a plain string literal so it can be checked
# here; anything else (an expression, a missing `to`) is reported rather than silently skipped.
DASHBOARD_LINK_TAG = re.compile(r"<DashboardLink\b([^>]*)>")
DASHBOARD_LINK_TO = re.compile(r'\bto="([^"]*)"')
DASHBOARD_LINK_IMPORT = re.compile(
    r'^import\s*\{[^}]*\bDashboardLink\b[^}]*\}\s*from\s*"/snippets/dashboard-link\.jsx";?\s*$',
    re.M,
)
RAW_DEEP_LINK = re.compile(r"bot\.bifrost\.gg/go(?:/([A-Za-z0-9_/-]*))?")

# A key is at least two dot-separated lowercase segments. Matched only inside backticks.
KEY_IN_CODE = re.compile(r"`([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)`")
CMD_IN_CODE = re.compile(r"`/([a-z][a-z0-9-]*)((?: [a-z][a-z0-9-]*)*)`")

# Dotted strings that are not permission keys. Extend deliberately; each entry is a claim that
# this string will never be a key.
NOT_KEYS = re.compile(
    r"^(?:"
    r"\w+\.(?:mdx?|json|ts|tsx|js|py|txt|png|jpg|svg|yml|yaml|env|lock|sh|properties|conf|cfg|ini|toml|jar|zip)$"  # filenames
    r"|(?:heimdall|bifrost|discord|example|localhost)\..*"                      # hostnames
    r"|.*\.(?:com|gg|dev|io|net|org|uk|local)$"
    r"|\d+\..*"                                                                 # version-ish
    r")"
)

# Commands that exist outside the manifest: Discord's own, or another bot's, quoted as context.
IGNORED_COMMANDS = {"help"}

# An inline opt-out, matching how every other Heimdall check does it. Needed for two real cases
# that are not errors and cannot be pattern-matched away:
#
#   - A page teaching the *wrong* form on purpose. permissions.mdx says
#     "`confessions.log.view_author`, not `confessions.view_author`", so it necessarily contains a
#     key that does not exist. That sentence is the single most useful line on the page.
#   - A hypothetical. settings.mdx says "rename `/suggest` to `/feedback`", where `/feedback` is
#     an example of a name somebody might choose, not a command that ships.
#
# Placed on the flagged line, or on a line shortly above it. The lookback is three lines rather
# than one because prose wraps: the marker introduces a sentence, and the string it excuses can
# easily be on the sentence's second or third line.
IGNORE_MARKER = re.compile(r"docs-manifest-ignore\s*--")
IGNORE_LOOKBACK = 3


def load_manifest(path):
    if not os.path.exists(path):
        sys.exit(f"manifest not found: {path}\nPass the path to heimdall-features.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_dashboard_links(path):
    if path is None:
        return None
    if not os.path.exists(path):
        sys.exit(f"dashboard links not found: {path}\nPass the path to dashboard-links.json")
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    keys = set()
    for link in data["links"]:
        keys.add(link["key"])
        keys.update(link.get("aliases", []))
    return keys


def collect(manifest):
    keys, commands, docs_paths = set(), {}, {}
    for plugin in manifest["plugins"]:
        for perm in plugin.get("permissions", []):
            keys.add(perm["key"])
        for cmd in plugin.get("commands", []):
            commands[cmd["name"]] = set(cmd.get("subcommands", []))
        if plugin.get("docsPath"):
            docs_paths[plugin["name"]] = plugin["docsPath"]
    return keys, commands, docs_paths


# Repository metadata, not published pages. AGENTS.md and CONTRIBUTING.md discuss the wrong forms
# on purpose - AGENTS.md documents this very check by quoting what it caught - and Mintlify does not
# publish them. Checking them would mean littering contributor docs with ignore markers to protect
# readers who are not the audience.
NOT_PUBLISHED = {"AGENTS.md", "CONTRIBUTING.md", "README.md", "CHANGELOG.md", "LICENSE.md"}


def mdx_files():
    for root, dirs, files in os.walk("."):
        dirs[:] = [
            d for d in dirs if d not in {".git", ".github", "node_modules", "images", "logo", "drafts"}
        ]
        for name in files:
            if name in NOT_PUBLISHED or name.endswith(".draft.mdx"):
                continue
            if name.endswith((".mdx", ".md")):
                yield os.path.join(root, name)


def main():
    manifest = load_manifest(MANIFEST)
    keys, commands, docs_paths = collect(manifest)
    link_keys = load_dashboard_links(DASHBOARD_LINKS)
    deep_links_checked = 0
    problems = []

    generated = {"reference/commands.mdx", "reference/permission-keys.mdx"}

    for path in sorted(mdx_files()):
        rel = os.path.relpath(path, ".")
        # The generated pages come from the manifest, so checking them against it proves nothing
        # and would just double-report a stale generator.
        if rel in generated:
            continue
        with open(path, encoding="utf-8") as handle:
            text = handle.read()

        if link_keys is not None and "<DashboardLink" in text and not DASHBOARD_LINK_IMPORT.search(text):
            problems.append(
                f'{rel}  uses <DashboardLink> without `import {{ DashboardLink }} from "/snippets/dashboard-link.jsx";`'
            )

        lines = text.splitlines()
        for line_no, line in enumerate(lines, 1):
            window = lines[max(0, line_no - 1 - IGNORE_LOOKBACK) : line_no]
            if any(IGNORE_MARKER.search(candidate) for candidate in window):
                continue

            for match in KEY_IN_CODE.finditer(line):
                candidate = match.group(1)
                if NOT_KEYS.match(candidate) or candidate in keys:
                    continue
                problems.append(f"{rel}:{line_no}  unknown permission key `{candidate}`")

            if link_keys is not None:
                for match in DASHBOARD_LINK_TAG.finditer(line):
                    to = DASHBOARD_LINK_TO.search(match.group(1))
                    deep_links_checked += 1
                    if not to:
                        problems.append(f'{rel}:{line_no}  <DashboardLink> needs a literal to="..."')
                    elif to.group(1) not in link_keys:
                        problems.append(f"{rel}:{line_no}  unknown dashboard link `{to.group(1)}`")
                for match in RAW_DEEP_LINK.finditer(line):
                    key = (match.group(1) or "").strip("/") or "overview"
                    deep_links_checked += 1
                    if key not in link_keys:
                        problems.append(f"{rel}:{line_no}  unknown dashboard link `{key}`")

            for match in CMD_IN_CODE.finditer(line):
                name = match.group(1)
                subpath = match.group(2).strip()
                if name in IGNORED_COMMANDS:
                    continue
                if name not in commands:
                    problems.append(f"{rel}:{line_no}  unknown command `/{name}`")
                    continue
                if subpath:
                    dotted = ".".join(subpath.split())
                    subs = commands[name]
                    # A subcommand group is stored dotted; a bare subcommand is not. Accept a
                    # documented prefix of a real path, since pages legitimately refer to a group.
                    if subs and not any(s == dotted or s.startswith(f"{dotted}.") for s in subs):
                        problems.append(
                            f"{rel}:{line_no}  `/{name} {subpath}` is not a subcommand of /{name}"
                        )

    for plugin, docs_path in sorted(docs_paths.items()):
        if not (os.path.exists(f"{docs_path}.mdx") or os.path.exists(f"{docs_path}.md")):
            problems.append(f"(manifest)  {plugin} declares docsPath '{docs_path}' with no page")

    if problems:
        print(f"[docs-manifest] {len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  {problem}")
        print(
            "\nEach is a page claiming something the bot no longer has. Fix the page, or if the\n"
            "bot changed deliberately, regenerate the reference pages too."
        )
        sys.exit(1)

    print(
        f"[docs-manifest] OK - checked {len(keys)} keys and {len(commands)} commands "
        f"against every page, and {len(docs_paths)} declared docsPath(s) all have one."
    )
    if link_keys is None:
        print("[docs-manifest] dashboard links NOT checked: no dashboard-links.json passed")
    else:
        print(f"[docs-manifest] {deep_links_checked} dashboard link(s) all name a real page.")


if __name__ == "__main__":
    main()
