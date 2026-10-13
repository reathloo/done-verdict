---
name: done-verdict
description: Verify whether a completed code change or release is actually ready. Use for questions like "is this fix done?", "the tests pass, can I ship?", or "is this release ready?" Check current evidence, separate tested behavior from runtime or publication claims, and name the next useful check.
---

# Done Verdict

Answer a completion or release-readiness question with the smallest useful set of current checks and a decision the user can act on. Do not activate for an ordinary request to implement, debug, review, or deploy something unless the user also asks whether it is verified or ready.

## Decide what to verify

1. Pin the claim and target: changed behavior, working tree or commit, build artifact, or proposed release. Separate distinct claims such as “tests pass” and “users can install it.” If no target is given, use the current project and change under discussion. Note which source/ref and environment supplied evidence belongs to.
2. Read applicable project instructions and inspect the relevant change and existing check entry points. For a release claim, read [release evidence](references/release-evidence.md) before selecting checks; for ordinary changes, read it only if distribution, signing, remote CI, or public availability matters.
3. Choose the cheapest checks that could change the answer. Prefer project-provided commands and the actual user path when the claim depends on one. Inspect scripts for likely side effects first. Verification alone does not authorize deployment, live-data changes, or other consequential writes. Use prescribed project dependencies when needed, but do not add verification tools or project files merely to answer a verification-only request. Stop when more checks would not improve the decision proportionately.
4. Run the safe checks within the user's scope. For each, retain the command or observation, result, source state, and claim it bears on. A check is “run” only if its result was actually returned; otherwise say `not run`. Reading test code is not executing it.

## Give the verdict

Use one status per claim; translate the labels naturally when replying in another language:

- `supported`: current evidence covers the claim in the stated scope.
- `partly supported`: evidence covers some parts, but a material part remains unverified.
- `unknown`: no decisive current evidence is available, or the relevant check was blocked.
- `contradicted`: current evidence conflicts with the claim.

Keep evidence boundaries explicit. An older or wrong-ref log does not prove the current change. A missing runner or inaccessible CI is inconclusive about product behavior. Conflicting runs indicate instability; do not select only the favorable run. A failing test establishes a mismatch, but not which side is wrong without a requirement. A green suite does not cover skipped or deselected tests. Unit tests prove only their covered behavior; a build or server launch does not prove the user path; a push does not prove publication; a listed artifact does not prove anonymous download or installation.

Reply briefly in the user's language with the verdict, decisive evidence (including the actual result when a check ran), the most important gap, and one actionable next check. For multiple claims, report them separately. For example: “Source checks: supported — 12 tests passed on this commit. Clean installation: unknown — not attempted. Next: install this exact artifact in a fresh environment.” If the requested claim is fully supported, say so without inventing another gate.

Do not turn verification into code review, test-writing, or release execution unless requested. Preserve the user's authorization boundaries. Never treat a simulated check as proof of a real-device, permission, installer, or public-user path.
