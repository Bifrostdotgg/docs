#!/usr/bin/env python3
"""Render reference/permission-keys.mdx from Heimdall's feature manifest.

Why this page exists: the keys were already correct on every feature page, and the AI
knowledgebase still answered `confessions.view_author` when asked, because the real key is
`confessions.log.view_author`. It had composed the key from the category and the action and
dropped the middle segment rather than quoting it.

That matters more than a normal docs error. An unknown key in Heimdall resolves to denied
and logs at info, so a role assigned a reconstructed key looks configured and silently does
nothing.

One page holding every exact string, grouped and labelled, gives retrieval a dense chunk to
quote from instead of a sentence to paraphrase. It is also the page to link anybody who asks
"what is the key for X".

Run from the docs repo root:
    python3 scripts/gen-permission-keys.py path/to/heimdall-features.json
"""
import json
import sys

MANIFEST = sys.argv[1] if len(sys.argv) > 1 else "heimdall-features.json"
OUT = "reference/permission-keys.mdx"

data = json.load(open(MANIFEST, encoding="utf-8"))
plugins = [p for p in data["plugins"] if p.get("permissions")]
total = sum(len(p["permissions"]) for p in plugins)

lines = [
    "---",
    'title: "Permission keys"',
    'description: "Every permission key Heimdall recognises, exactly as it must be written."',
    'icon: "key"',
    "---",
    "",
    "<Note>",
    "  Generated from the bot source. If a key is not on this page, it does not exist.",
    "</Note>",
    "",
    "## Copy keys exactly, never reconstruct them",
    "",
    "A key has two or three parts:",
    "",
    "```",
    "category.action",
    "category.subcategory.action",
    "```",
    "",
    "Most keys have three. `confessions.log.view_author` is not `confessions.view_author`, and",
    "`tickets.operations.claim_tickets` is not `tickets.claim`. The middle segment is part of",
    "the key, not a description of where it lives.",
    "",
    "**A key that does not exist is silently refused.** Heimdall resolves an unrecognised key to",
    "denied and records it in its log at info level. Nothing in the dashboard marks it as wrong,",
    "so the only symptom is a role that appears configured and cannot use the feature. If a",
    "permission you granted seems to do nothing, check the key against this page first.",
    "",
    f"Heimdall recognises **{total} keys** across **{len(plugins)} features**.",
    "",
]

for p in sorted(plugins, key=lambda x: x["name"]):
    title = p["name"].replace("-", " ").title()
    lines.append(f"## {title}")
    lines.append("")
    if p.get("docsPath"):
        lines.append(f"[Feature documentation](/docs/{p['docsPath']})")
        lines.append("")
    lines.append("| Permission key | Grants |")
    lines.append("| --- | --- |")
    for entry in p["permissions"]:
        label = entry.get("label") or ""
        desc = entry.get("description") or ""
        # Label and description together, because the label alone is often just a restatement
        # of the key and tells a reader nothing new.
        grants = f"**{label}**. {desc}".strip().rstrip(".") + "." if label or desc else "See the feature page."
        grants = grants.replace("|", "\\|")
        lines.append(f"| `{entry['key']}` | {grants} |")
    lines.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")
print(f"wrote {OUT}: {total} keys across {len(plugins)} features")
