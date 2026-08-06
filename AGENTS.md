# Documentation project instructions

## About this project

- Documentation site for [Heimdall](https://github.com/Bifrostdotgg/Heimdall), built on [Mintlify](https://mintlify.com)
- Pages are MDX files with YAML frontmatter
- Configuration lives in `docs.json`
- Run `mint dev` to preview locally
- Run `mint broken-links` to check links

## The split: generated reference, hand-written narrative

**Reference material is generated and must not be hand-edited.** Commands, subcommands and
permission keys come from Heimdall's own source, published as
`docs/generated/heimdall-features.json` in that repo.

| File | Source |
|------|--------|
| `reference/commands.mdx` | Generated. Run `python3 scripts/gen-commands.py <path-to>/heimdall-features.json` |

Everything else is written by hand, because "why would I turn this on" cannot be generated.

This split exists because the alternative was tried and failed. Before 2026-08-05 these
docs were maintained entirely by hand, and had drifted to: 52 of 92 permission keys naming
actions that did not exist, 12 features with no page at all, 22 commands undocumented, and
24 documented commands that had been folded into subcommands. Nobody was careless. Two
copies of the same executable facts always diverge, and only one of them runs.

## When Heimdall ships a feature or a change

The Heimdall build enforces the first two steps, so they are not optional:

1. **`check:plugin-docs`** fails unless the plugin's `manifest.json` declares a `docsPath`,
   the page path on this site (for example `community/confessions`).
2. **`check:docs-manifest`** fails when the committed feature manifest no longer matches the
   code, so a renamed command or permission key cannot land silently.
3. **Write or update the page** at the declared `docsPath` in this repo.
4. **Regenerate `reference/commands.mdx`** if commands changed.

A `docsPath` pointing at a page that does not exist yet is the intended state while a
feature is in flight. It is a promissory note the build can see.

## Terminology

- **Feature**, not plugin. "Plugin" is Heimdall's internal word for the same thing and means
  nothing to a server owner.
- **Server**, not guild. Discord's UI says server everywhere.
- **Member**, not user, when talking about somebody in a server.
- **Dashboard** for the web app. Not "panel", not "web UI".
- **Permission key** for the dotted strings such as `confessions.log.view_author`.

## Style preferences

- Use active voice and second person ("you")
- Keep sentences concise, one idea per sentence
- Use sentence case for headings
- Bold for UI elements: Click **Settings**
- Code formatting for file names, commands, paths, and code references
- **No em dashes, ever.** Use a plain hyphen, or restructure with a comma, a colon, or two
  sentences. This applies across the whole Bifrost codebase and is enforced in the Heimdall
  repo by a test.

## What every feature page should answer

The pages written on 2026-08-05 follow this shape. It exists because these are the questions
support gets asked:

1. What does this do, in one paragraph, in terms of what the reader gets.
2. What has to be true before it works. Permissions the bot needs, other features it depends
   on, anything that only counts from the moment it is enabled.
3. How to set it up. A settings table beats prose.
4. The gotcha. Every feature has one, and it is the single most valuable paragraph on the
   page. Rate limits that make something look broken when it is not, data that cannot be
   backfilled, an emoji kind Discord will not accept.
5. Required permissions, as a table of action against key. Keys must match the generated
   manifest exactly.

## Content boundaries

- Do not document internal features. `lib`, `dev`, `console`, `file-storage`,
  `bifrost-customers` and `support-core` are listed as internal in Heimdall's
  `checkPluginDocs.ts` and have no public surface.
- Do not document payout rates, pricing tiers or contractual terms. Those live outside the
  docs and go stale differently.
- Do not invent permission keys or settings. If you cannot find it in the source or the
  manifest, it does not exist.
