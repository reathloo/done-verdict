---
name: done-verdict
description: Check whether a public GitHub Release is actually published for an intended tag commit, whether a selected CI workflow passed on that commit, and whether a named asset downloads with matching size and SHA-256. Use for release-ready, published-release, wrong-tag, CI-on-tag, or public-download questions; not ordinary feature completion.
---

# Done Verdict

Produce a bounded, repeatable verdict for **one public GitHub Release**. The script turns GitHub observations into separate claims; it does not decide that a product is universally “ready.” Do not use this workflow for ordinary code completion, generic tests, private repositories, or non-GitHub distribution.

## Fast path

1. Pin `OWNER/REPO` and the exact release `TAG` from the user's request, relevant project config, or repository. If the intended revision is the current local commit, read project instructions and use `git rev-parse HEAD` for `--expected-commit`; a tag resolving to *some* commit is weaker evidence than matching the intended commit. Never silently substitute the latest tag or `main`.
2. From this skill directory, run the Python 3.9+ standard-library checker:

   ```sh
   python3 scripts/release_proof.py --repo OWNER/REPO --tag TAG --expected-commit FULL_40_CHARACTER_SHA
   ```

   Omit `--expected-commit` only when no intended SHA can be established; then report only that the tag resolves. The checker uses anonymous, read-only HTTP and prints JSON. Exit 0 means **collection completed**, not “release passed”; exit 2 means invalid arguments.
3. Add only the checks the user actually needs:

   | Question | Additional flags | Evidence boundary |
   | --- | --- | --- |
   | Did one workflow pass on this commit? | `--workflow ci.yml` | Checks the latest run found for that workflow and tag commit, not all CI. |
   | Is an asset listed? | `--asset exact-name.zip` | Metadata only; no public download proof. |
   | Can an anonymous user fetch it? | `--asset exact-name.zip --download` | In-memory fetch, listed size, and SHA-256; no installation. |
   | Does it match a known digest? | Add `--sha256 HEX` to the download | Compares both the supplied digest and GitHub's asset digest when available. |

   Do not guess workflow or asset names. Inspect the release/repository read-only or ask for the intended one. The default download cap is 50 MB; `--max-bytes` may be raised to 500 MB only when the larger fetch is relevant.

## Interpret, then answer

- Read `requested`, `observed_at`, and **each** `claims[]` item (`status`, `detail`, `source`). An omitted optional check was **not checked**, not successful. `supported` means the observed narrow claim holds; `contradicted` means direct evidence conflicts; `unknown` means unavailable, pending, malformed, or not decisive. A 403/rate limit is unknown, not a failed release.
- The checker verifies an actual Git **tag ref**, including annotated tags; a same-named branch is not a tag. It also marks a published prerelease as a *prerelease*, not a stable release. A CI success on the same commit does not prove every workflow passed or that the release artifact came from that run.
- Report the target, observed tag SHA, relevant claim statuses and decisive evidence, then the largest unresolved user claim and one useful next check. If the claim is fully supported within its stated scope, stop there. Example: “Tag `v1.2.3`: supported — points to expected SHA. Public release: supported — published prerelease. Download: unknown — not requested. Installation: unknown — not tested.”
- A listed asset is not a successful anonymous download; a downloaded asset is not an installed, signed, or working product. Read [release evidence boundaries](references/release-evidence.md) when the user asks about installation, platform trust, stores, privacy/offline behavior, or other claims beyond this checker.

The checker itself never publishes, installs, or executes artifacts. Do not infer permission to do those things from a request for a verdict; if separately requested, handle them as separate scoped tasks. For a non-GitHub release, explain that this check does not apply and rely only on actual project-specific evidence.
