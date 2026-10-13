---
name: done-verdict
description: Evidence-based verification for completed code changes and release readiness. Use when someone asks "is this feature or fix done?", "the tests pass, can I ship?", or "is this release ready?" Run relevant existing checks and distinguish proven behavior from missing runtime, CI, or publication evidence.
---

# Done Verdict

Answer the user's completion question with the smallest useful set of current checks and a precise conclusion.

## Workflow

1. Identify the claim and target: the changed behavior, commit or working tree, build artifact, or proposed release. If no target is given, use the current project and the change under discussion. Note the source/ref and environment to which any supplied test log or CI result belongs.
2. Read applicable project instructions and inspect the relevant diff, scripts, and CI or packaging configuration. Choose checks that can change the answer. Prefer project-provided commands and a real integration path when the claim depends on one.
3. Run safe, relevant checks within the user's authorized scope. Inspect a check's likely side effects before running it; verification alone does not authorize deployment, live-data changes, or other consequential writes. Use the project's prescribed dependencies when needed, but avoid adding new verification tools or project files for a verification-only request. Record the command or observation, actual tool result, and which claim it supports. Stop once further checks would not improve the answer proportionately.
4. Match every conclusion to its evidence. Use `supported`, `partly supported`, `unknown`, or `contradicted`; give separate statuses for distinct claims.
   - Currentness: Logs from an older source state, a different ref, or the wrong environment do not prove the current claim.
   - Execution: Report a command as executed only when its output or exit status was actually returned. If blocked, say `not run`; inspection of source or test code is not a test result.
   - Interpretation: Missing tooling, permissions, or infrastructure makes a check inconclusive about product behavior. If runs conflict without a source change, disclose the instability rather than select the favorable result. When a test and implementation disagree, state the mismatch without deciding which expectation is wrong unless a requirement establishes it.
   - Scope: A passing unit test supports only the behavior it tests. A build or an app/server launch does not establish the user path. A push does not establish publication. A local artifact does not establish public download or installation.
5. If the user asks about a release, read [release evidence](references/release-evidence.md). For ordinary changes, read it only when distribution, signing, remote CI, or public availability affects the answer.
6. Reply briefly in the user's language: status, the decisive evidence, the most important remaining gap if any, and one actionable next check. Name a command, environment, or person when that makes the next step concrete. If the requested claim is fully supported, say so without inventing extra work.

Do not turn this verification request into a code review, test-writing task, or release operation unless the user asked for those actions. Follow the user's existing authorization for any requested implementation or publication. Never infer that a simulated check proves a real-device, permission, installer, or public-user path.
