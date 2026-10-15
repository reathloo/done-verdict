---
name: done-verdict
description: Verify a public GitHub release against its exact tag commit, published release, optional GitHub Actions run, and downloadable asset. Use when someone asks whether a tagged release is really live, whether CI passed for that exact revision, or whether users can fetch a release asset. Distinguish these proofs from installation and runtime behavior.
---

# Done Verdict

Produce a bounded, repeatable evidence verdict for one public GitHub release. Do not activate for ordinary code completion, generic test-running, or a release that does not use public GitHub Releases. Never publish, install, or execute an artifact as part of verification.

## Check the exact claim

1. Identify `OWNER/REPO` and exact `TAG`. If the user means the current local commit, read the project's instructions and obtain its full SHA with `git rev-parse HEAD`; pass it as `--expected-commit`. Do not assume the local checkout matches the release.
2. Run `python3 scripts/release_proof.py --repo OWNER/REPO --tag TAG --expected-commit FULL_SHA` from this skill directory. The script requires Python 3.9+, uses only its standard library and anonymous, read-only HTTP. It prints JSON; exit 0 means evidence collection completed, **not** that all claims passed. Exit 2 means invalid input.
3. Add only checks relevant to the question: `--workflow ci.yml` for one named GitHub Actions workflow; `--asset exact-name.zip --download` for an anonymous download; optionally `--sha256 HEX` for a known expected digest. Download is limited to 50 MB by default, with `--max-bytes` available up to 500 MB. Do not guess an asset or workflow name; inspect the repository if needed.
4. Read each claim's `status`, `detail`, and `source`. `supported` means the stated observation succeeded; `contradicted` means it conflicts with the claim; `unknown` means unavailable, pending, or untested. Treat a 403/rate limit as unknown. A listed asset is not a successful download; a successful download is not an installation or a trusted runtime. If no workflow or asset was selected, those claims were not checked.

Use [release evidence boundaries](references/release-evidence.md) only for claims outside this script's scope. If the user asks about a non-GitHub release, this deterministic check does not apply; answer from actual project-specific evidence without inventing an equivalent automated proof.

## Answer

Report the target tag and observed commit, then the relevant claim statuses with the decisive result. State the largest remaining gap and one concrete next check only when needed. Keep distinct claims distinct; never collapse a successful tag lookup into “release ready.” If the user asks whether an artifact **works after installation**, say `unknown` unless that exact artifact was independently installed and exercised in the target environment. Do not claim remote CI, public availability, platform trust, or installation from local tests or a Git push.
