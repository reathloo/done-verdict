# Shipproof

Shipproof helps a coding agent verify a completed feature or bug fix and assess release readiness: **What is actually proven, and what should I check next?** It inspects the relevant project state, runs suitable existing checks, and reports only claims those checks support.

Typical prompts:

- “Is this fix ready to call done? Verify the changed behavior.”
- “Is this feature done, or are the passing tests missing a real integration path?”
- “Can I ship this build? Check the release evidence.”
- “The tests pass. What remains unverified?”

The default response is short and stays in chat. Shipproof does not require project configuration or a separate reporting service. It uses existing project instructions and commands, and it distinguishes local tests, real runtime behavior, remote CI, and public distribution.

Shipproof is for checking a completion claim, not for general test generation, code review, or deployment automation. It does not claim that a passing build proves the app works for users.

For example, if unit tests pass but nobody has installed the built artifact, Shipproof should report the tested behavior as supported and the installation claim as still unknown. The useful next step is a clean installation of that exact artifact—not another generic test run. This is an illustration of the decision it makes, not a claim that every project needs an installer test.

## Install

The installable skill is in [`skills/shipproof/`](skills/shipproof/SKILL.md). Install it with the skills CLI:

```sh
npx skills add reathloo/shipproof --skill shipproof
```

The [skills.sh page](https://www.skills.sh/reathloo/shipproof/shipproof) shows the public listing. A listing is not the same as a top search position or an independent quality endorsement.

The skill is plain Markdown; it requires no account, service, or project-specific configuration. The CLI downloads the current version from GitHub. Review the skill before installing it in a project, as you would with any agent instructions.

## Current state

This is an early public version. Its package structure and local installation have been checked, and initial behavioral smoke tests caught and corrected two unsupported conclusions. Broader cross-project comparisons and independent user trials are still open. Do not treat an install count or a passing example as proof that the skill is reliable in every project.

If Shipproof makes an unsupported claim or misses an important check, [open an issue](https://github.com/reathloo/shipproof/issues) with the question, the evidence the agent actually saw, and the expected decision. Please remove private code, credentials, and personal data before sharing logs.

## License

MIT. See [`LICENSE`](LICENSE).
