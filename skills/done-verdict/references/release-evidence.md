# Evidence outside the public GitHub release check

The script checks only the public tag commit, published release metadata, one optional GitHub Actions workflow run bound to that commit, and one optional listed/anonymous-downloaded asset. It never proves all workflows are green, that a release is stable rather than a prerelease, or that an asset installs, launches, is signed, is accepted by a platform/store, or behaves correctly for users.

For those claims, use evidence from the exact artifact and target environment:

| Claim | Useful additional evidence |
| --- | --- |
| Installs and runs | Fresh installation and actual user path with the downloaded asset |
| Platform trust | Signature, notarization, or store acceptance of that asset |
| Browser-store availability | Public store listing and installed-browser behavior |
| Runtime privacy/offline behavior | Network and dependency observations during the actual user path |

Do not run installers or touch external publication state merely because someone asked for a verdict. Report `unknown` for untested claims and name the next safe check.
