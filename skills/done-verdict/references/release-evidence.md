# Release evidence boundaries

Read this only when a question extends beyond the checker's GitHub observations. The checker verifies an actual tag ref and its commit, published release metadata, one optional same-commit workflow, and one optional asset listing/download. It cannot establish an end-to-end chain from source through build to installed behavior.

| User claim | What the checker establishes | What remains unproven |
| --- | --- | --- |
| “The intended commit was released” | Tag ref resolves to the expected SHA; release is published for that tag | The source built into an asset is identical to that commit |
| “CI passed” | Selected workflow's latest matching run completed successfully on the tag commit | Every workflow, matrix job, or later deployment succeeded |
| “Users can get the artifact” | Named asset is listed; optional anonymous retrieval matches listed size and available SHA-256 expectations | Installation, signature, trust, platform behavior |
| “This is stable” | Release metadata says published and whether `prerelease` is true | Product maturity or production fitness |

The checker reports `unknown` for unavailable/pending checks (for example, an API rate limit or no matching CI run). A direct mismatch is `contradicted` (for example, wrong expected SHA, missing named asset, failed matching run, or wrong digest). Do not convert either into a universal product judgment.

For downstream claims, use the **exact downloaded artifact** and intended environment:

| Claim | Useful additional evidence |
| --- | --- |
| Installs and runs | Fresh installation and actual user path with the downloaded asset; record platform/version |
| Platform trust | Signature, notarization, or store acceptance of that asset |
| Browser-store availability | Public store listing and installed-browser behavior |
| Runtime privacy/offline behavior | Network and dependency observations during the actual user path |

Do not run installers or touch external publication state merely because someone asked for a verdict. Report `unknown` for untested claims and name the next check that would resolve the user's actual question. A GitHub prerelease can be publicly downloadable while still not being a stable release. A Git push, release page, asset listing, anonymous download, and successful installation are separate observations.
