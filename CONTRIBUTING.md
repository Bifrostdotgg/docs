> **Customize this file**: Tailor this template to your project by noting specific contribution types you're looking for, adding a Code of Conduct, or adjusting the writing guidelines to match your style.

# Contribute to the documentation

Thank you for your interest in contributing to our documentation! This guide will help you get started.

## Target `staging`, not `main`

All contributions target the `staging` branch (the repository default). Never open a pull
request against `main`. `main` is the live site, and it only advances through the automatic
promotion workflow that runs when Heimdall ships a release, or by hand from this repo's
`promote.yml` workflow as a fallback. A PR opened against `main` will need to be redirected
to `staging` before it can be reviewed.

One consequence: CI on `staging` checks your pages against Heimdall's `main` branch manifest,
while CI on `main` checks against Heimdall's `release` branch manifest. So a page can be
correct against `staging`'s CI and still describe a feature that has not shipped to
production yet, that gap is expected and closes automatically when Heimdall releases.

## How to contribute

### Option 1: Edit directly on GitHub

1. Navigate to the page you want to edit, on the `staging` branch
2. Click the "Edit this file" button (the pencil icon)
3. Make your changes and submit a pull request against `staging`

### Option 2: Local development

1. Fork and clone this repository
2. Install the Mintlify CLI: `npm i -g mint`
3. Create a branch for your changes, based on `staging`
4. Make changes
5. Navigate to the docs directory and run `mint dev`
6. Preview your changes at `http://localhost:3000`
7. Commit your changes and submit a pull request against `staging`

For more details on local development, see our [development guide](development.mdx).

## Writing guidelines

- **Use active voice**: "Run the command" not "The command should be run"
- **Address the reader directly**: Use "you" instead of "the user"
- **Keep sentences concise**: Aim for one idea per sentence
- **Lead with the goal**: Start instructions with what the user wants to accomplish
- **Use consistent terminology**: Don't alternate between synonyms for the same concept
- **Include examples**: Show, don't just tell
