#!/usr/bin/env python3
"""Render reference/commands.mdx from Heimdall's feature manifest.

The hand-maintained version of this page was wrong in both directions: 22 commands
existed that it did not list, and 24 it listed had been folded into subcommands of
/games and /economy. That is what a hand-maintained mirror of executable facts always
becomes, so this page is generated instead.

Run from the docs repo root with the manifest path as the argument:
    python3 gen-commands.py path/to/heimdall-features.json
"""
import json
import sys

MANIFEST = sys.argv[1] if len(sys.argv) > 1 else "heimdall-features.json"
OUT = "reference/commands.mdx"

data = json.load(open(MANIFEST, encoding="utf-8"))
plugins = [p for p in data["plugins"] if p["commands"]]

lines = [
    "---",
    'title: "Command reference"',
    'description: "Every slash command Heimdall registers, grouped by the feature that owns it."',
    'icon: "terminal"',
    "---",
    "",
    "<Note>",
    "  This page is generated from the bot source, so it cannot drift out of date. If a command",
    "  is missing here it does not exist.",
    "</Note>",
    "",
    "Commands marked **opt in** are only registered in servers that have enabled the feature.",
    "They are genuinely absent until then rather than hidden, so do not expect to see them",
    "before switching the feature on.",
    "",
]

total_cmds = sum(len(p["commands"]) for p in plugins)
total_subs = sum(len(c["subcommands"]) for p in plugins for c in p["commands"])
lines += [
    f"Heimdall registers **{total_cmds} commands** with **{total_subs} subcommands** across",
    f"**{len(plugins)} features**.",
    "",
]

for p in sorted(plugins, key=lambda x: x["name"]):
    title = p["name"].replace("-", " ").title()
    lines.append(f"## {title}")
    lines.append("")
    if p.get("docsPath"):
        lines.append(f"[Feature documentation](/docs/{p['docsPath']})")
        lines.append("")

    for c in sorted(p["commands"], key=lambda x: x["name"]):
        flag = " **opt in**" if c["optIn"] else ""
        desc = c["description"] or "No description."
        lines.append(f"### `/{c['name']}`{flag}")
        lines.append("")
        lines.append(desc)
        lines.append("")
        if c["subcommands"]:
            lines.append("| Subcommand |")
            lines.append("| --- |")
            for s in c["subcommands"]:
                lines.append(f"| `/{c['name']} {s.replace('.', ' ')}` |")
            lines.append("")

    if p["permissionKeys"]:
        lines.append("Permission keys:")
        lines.append("")
        for k in p["permissionKeys"]:
            lines.append(f"- `{k}`")
        lines.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")
print(f"wrote {OUT}: {total_cmds} commands, {total_subs} subcommands, {len(plugins)} features")
