# Release evidence boundaries

Read this reference when the user asks whether a build can be distributed, released, or called publicly available.

| Claim | Evidence that can support it | Common false shortcut |
| --- | --- | --- |
| Source checks pass | Successful, relevant checks on the current source state | Earlier run before later edits |
| Artifact builds | Successful package build and inspected output | A successful source compilation alone |
| Artifact installs or runs | Installation or launch of the built artifact in the intended environment | Build success or a synthetic UI fixture |
| Commit reached remote | Remote ref points to the intended commit | Local commit or push command without remote confirmation |
| Remote CI passed | Successful current workflow run for the intended ref | Local tests, old green run, or missing workflow |
| Release is public | Published, non-draft release with expected assets | Tag pushed or draft release created |
| Download works | Anonymous retrieval of the expected asset; checksum where provided | Asset list visible to an authenticated maintainer |
| Platform trust works | Target platform accepts the actual distributed artifact | Ad hoc signature, local bypass, or unsigned package |

The exact evidence depends on the product. For a library, compatibility checks may matter more than an installer. For a browser extension, store submission and installed-browser behavior are distinct from a Git push. For privacy or offline claims, source inspection alone is insufficient when runtime network or bundled dependencies determine the behavior.

Tie remote checks to the intended revision and inspect the actual artifact when the claim concerns distribution. If a necessary check is unavailable, call it `unknown` and give a practical way to obtain it. Do not turn an unavailable check into a failure or success.
