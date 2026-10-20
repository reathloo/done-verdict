# Done Verdict

Done Verdict gives a coding agent a repeatable answer to one narrower question: **Is this exact public GitHub release actually available, and what part remains unproven?** Its read-only Python checker verifies the real Git tag ref and commit (not a same-named branch), published release, optional exact-commit GitHub Actions run, and optional anonymous asset download with size and SHA-256 checks.

Typical prompts:

- “Is `v1.2.3` really published for this commit?”
- “Did `ci.yml` pass for the commit behind this tag?”
- “Can a user download `app.zip` anonymously, and does its checksum match?”

The checker uses Python 3.9+'s standard library, requires no account or token, and does not modify the repository or run downloaded files. Its JSON output keeps each claim separate. For example:

```sh
python3 skills/done-verdict/scripts/release_proof.py \
  --repo owner/project --tag v1.2.3 --expected-commit FULL_40_CHARACTER_SHA \
  --workflow ci.yml --asset app.zip --download
```

Replace the placeholders with the exact repository, tag, intended full commit SHA, workflow filename, and release-asset name. Omit optional flags when those claims are not part of the question. The result records what was requested and when it was observed; `supported`, `contradicted`, and `unknown` are reported per claim. A zero process exit code means the check ran, **not** that every claim passed. When both `--sha256` and GitHub's asset digest exist, both must agree with the downloaded bytes for the checksum claim to be supported. A published prerelease is identified as a prerelease.

This does **not** prove that the artifact installs, runs, came from the successful CI run, is signed, or is accepted by an app store. It is not a generic feature-verification skill, deployment tool, or substitute for target-platform testing.

For example, if a published release and anonymous download are confirmed but nobody has installed the artifact, a useful answer looks like this:

> Public release: **supported** — tag `v1.2.3` resolves to the expected commit and the release is published.
>
> Anonymous download: **supported** — `app.zip` was fetched and its SHA-256 matched.
>
> Clean installation: **unknown** — the downloaded artifact has not been installed.
>
> Next: install this exact artifact in a fresh target environment.

The output is evidence, not a universal “ship it” score. The next check should address the user's actual remaining claim.

## Install

The installable skill is in [`skills/done-verdict/`](skills/done-verdict/SKILL.md). Install it with the skills CLI:

```sh
npx skills add reathloo/done-verdict --skill done-verdict
```

The [skills.sh page](https://www.skills.sh/reathloo/done-verdict/done-verdict) shows the public listing. A listing is not the same as a top search position or an independent quality endorsement.

The CLI downloads the current published version from GitHub. The checker requires Python 3.9+ and network access to public GitHub endpoints when run. Review any agent instructions before installing them in a project.

## Current state

The public `v0.3.1` skill includes the real-tag check, prerelease labeling, and comparison of both available SHA-256 expectations. Unit tests and public-release smoke tests do not prove broad reliability or incremental value over an unaided agent; cross-project comparisons and independent user feedback remain open. Do not treat an install count as a quality endorsement.

If Done Verdict makes an unsupported claim or misses an important check, [open an issue](https://github.com/reathloo/done-verdict/issues) with the question, the evidence the agent actually saw, and the expected decision. Please remove private code, credentials, and personal data before sharing logs.

## Migrating from Shipproof

Done Verdict was called Shipproof through `v0.1.1`. The old GitHub repository URL redirects, but the old skill ID `shipproof` is no longer provided by the current branch. Install `done-verdict` with the command above and remove any older `shipproof` installation from your agent. Existing installations do not change their skill name automatically; old release tags remain available for reference.

## License

MIT. See [`LICENSE`](LICENSE).
