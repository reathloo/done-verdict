#!/usr/bin/env python3
"""Read-only, anonymous evidence for one public GitHub release."""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


API = "https://api.github.com"
USER_AGENT = "done-verdict-release-proof/0.1"


class FetchError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def fetch(url, limit=2_000_000):
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            data = response.read(limit + 1)
            if len(data) > limit:
                raise FetchError("response exceeds size limit")
            return data
    except HTTPError as exc:
        raise FetchError("HTTP " + str(exc.code), exc.code) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise FetchError(type(exc).__name__) from exc


def get_json(path):
    try:
        return json.loads(fetch(API + path))
    except (ValueError, UnicodeError) as exc:
        raise FetchError("invalid JSON response") from exc


def claim(name, status, detail, source=None):
    result = {"claim": name, "status": status, "detail": detail}
    if source:
        result["source"] = source
    return result


def resolve_tag_commit(base, tag):
    """Follow an actual Git tag ref, not a same-named branch or commitish."""
    reference = get_json(base + "/git/ref/tags/" + quote(tag, safe=""))
    if not isinstance(reference, dict):
        raise FetchError("invalid tag reference response")
    if reference.get("ref") != "refs/tags/" + tag:
        raise FetchError("tag reference does not match requested tag")
    target = reference.get("object", {})
    seen = set()
    for _ in range(5):
        if not isinstance(target, dict):
            raise FetchError("invalid tag target response")
        kind, sha = target.get("type"), target.get("sha")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise FetchError("tag target has no full SHA")
        if kind == "commit":
            return sha
        if kind != "tag" or sha in seen:
            raise FetchError("tag target is not a commit or contains a cycle")
        seen.add(sha)
        try:
            tag_object = get_json(base + "/git/tags/" + sha)
        except FetchError as exc:
            raise FetchError("annotated tag object unavailable: " + str(exc)) from exc
        if not isinstance(tag_object, dict):
            raise FetchError("invalid annotated tag response")
        target = tag_object.get("object", {})
    raise FetchError("tag nesting exceeds safety limit")


def checksum_claim(expected_by_source, observed, source):
    details = []
    statuses = []
    for label, expected in expected_by_source:
        if not isinstance(expected, str) or not re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", expected):
            statuses.append("unknown")
            details.append(label + " has an unsupported digest format")
        else:
            expected_sha = expected.removeprefix("sha256:").lower()
            statuses.append("supported" if observed == expected_sha else "contradicted")
            details.append(label + " " + expected_sha)
    status = "contradicted" if "contradicted" in statuses else "unknown" if "unknown" in statuses else "supported"
    return claim("checksum", status, "; ".join(details) + "; observed " + observed, source)


def check(args):
    owner, repo = args.repo.split("/")
    base = "/repos/" + quote(owner) + "/" + quote(repo)
    tag = quote(args.tag, safe="")
    result = {
        "schema_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "repository": args.repo,
        "tag": args.tag,
        "requested": {"expected_commit": args.expected_commit, "workflow": args.workflow, "asset": args.asset, "download": args.download},
        "claims": [],
        "limits": ["Anonymous public access only", "No artifact installation or execution"],
    }
    claims = result["claims"]
    commit_url = API + base + "/git/ref/tags/" + tag
    sha = None
    try:
        sha = resolve_tag_commit(base, args.tag)
        if args.expected_commit and sha.lower() != args.expected_commit.lower():
            claims.append(claim("tag_commit", "contradicted", "Tag resolves to " + sha + ", not expected " + args.expected_commit, commit_url))
        else:
            claims.append(claim("tag_commit", "supported", "Tag resolves to " + sha, commit_url))
    except FetchError as exc:
        status = "contradicted" if exc.status == 404 else "unknown"
        claims.append(claim("tag_commit", status, str(exc), commit_url))

    release_url = API + base + "/releases/tags/" + tag
    release = None
    try:
        release = get_json(base + "/releases/tags/" + tag)
        if not isinstance(release, dict):
            raise FetchError("invalid release response")
        if release.get("draft") or not release.get("published_at"):
            claims.append(claim("public_release", "contradicted", "Release is draft or not published", release_url))
        else:
            channel = "prerelease" if release.get("prerelease") else "release"
            claims.append(claim("public_release", "supported", "Published " + channel + ": " + str(release.get("html_url", "")), release_url))
    except FetchError as exc:
        release = None
        status = "contradicted" if exc.status == 404 else "unknown"
        claims.append(claim("public_release", status, str(exc), release_url))

    if args.workflow:
        if not sha:
            claims.append(claim("workflow", "unknown", "Cannot bind workflow run to an unresolved tag commit"))
        else:
            workflow = quote(args.workflow, safe="")
            path = base + "/actions/workflows/" + workflow + "/runs?" + urlencode({"head_sha": sha, "per_page": 100})
            url = API + path
            try:
                runs = get_json(path).get("workflow_runs", [])
                matching = [run for run in runs if run.get("head_sha", "").lower() == sha.lower()]
                if not matching:
                    claims.append(claim("workflow", "unknown", "No run found for this exact commit", url))
                else:
                    latest = max(matching, key=lambda run: (run.get("created_at", ""), run.get("run_attempt", 0)))
                    state = latest.get("status")
                    conclusion = latest.get("conclusion")
                    if state == "completed" and conclusion == "success":
                        verdict = "supported"
                    elif state == "completed" and conclusion in {"failure", "timed_out", "action_required"}:
                        verdict = "contradicted"
                    else:
                        verdict = "unknown"
                    claims.append(claim("workflow", verdict, "Latest matching run: " + str(state) + "/" + str(conclusion), latest.get("html_url", url)))
            except (FetchError, AttributeError, TypeError) as exc:
                claims.append(claim("workflow", "unknown", str(exc), url))

    if args.asset:
        if release is None:
            claims.append(claim("asset_listed", "unknown", "Release metadata unavailable"))
        else:
            assets = release.get("assets", [])
            assets_valid = isinstance(assets, list)
            matches = (
                [asset for asset in assets if isinstance(asset, dict) and asset.get("name") == args.asset and asset.get("state") == "uploaded"]
                if assets_valid else []
            )
            if not assets_valid:
                claims.append(claim("asset_listed", "unknown", "Invalid release asset list", release_url))
            elif not matches:
                claims.append(claim("asset_listed", "contradicted", "Uploaded asset not listed: " + args.asset, release_url))
            else:
                asset = matches[0]
                claims.append(claim("asset_listed", "supported", "Uploaded asset listed: " + args.asset, release_url))
                if args.download:
                    asset_url = asset.get("browser_download_url", "")
                    parsed = urlparse(asset_url)
                    if parsed.scheme != "https" or parsed.hostname != "github.com":
                        claims.append(claim("anonymous_download", "unknown", "Unexpected asset URL; download refused"))
                    elif isinstance(asset.get("size"), int) and asset["size"] > args.max_bytes:
                        claims.append(claim("anonymous_download", "unknown", "Asset exceeds configured byte limit", asset_url))
                    else:
                        try:
                            data = fetch(asset_url, args.max_bytes)
                            digest = hashlib.sha256(data).hexdigest()
                            expected_size = asset.get("size")
                            if not isinstance(expected_size, int):
                                download_status = "unknown"
                            else:
                                download_status = "supported" if len(data) == expected_size else "contradicted"
                            claims.append(claim("anonymous_download", download_status, "Fetched " + str(len(data)) + " bytes; release lists " + str(expected_size) + " bytes; SHA-256 " + digest, asset_url))
                            expected = []
                            if args.sha256:
                                expected.append(("supplied SHA-256", args.sha256))
                            if asset.get("digest"):
                                expected.append(("GitHub asset digest", asset["digest"]))
                            if expected:
                                claims.append(checksum_claim(expected, digest, asset_url))
                        except FetchError as exc:
                            status = "contradicted" if exc.status in {404, 410} else "unknown"
                            claims.append(claim("anonymous_download", status, str(exc), asset_url))
        result["limits"].append("Asset installation and target-platform trust remain untested")

    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Public GitHub OWNER/REPO")
    parser.add_argument("--tag", required=True, help="Exact release tag")
    parser.add_argument("--expected-commit", help="Expected full 40-character commit SHA")
    parser.add_argument("--workflow", help="Optional GitHub Actions workflow file name or ID")
    parser.add_argument("--asset", help="Optional exact release asset name")
    parser.add_argument("--download", action="store_true", help="Fetch selected asset anonymously into memory")
    parser.add_argument("--sha256", help="Expected SHA-256 for downloaded asset")
    parser.add_argument("--max-bytes", type=int, default=50_000_000, help="Maximum asset download size (default: 50 MB)")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", args.repo):
        parser.error("--repo must be OWNER/REPO")
    if not args.tag or any(ord(char) < 32 for char in args.tag) or len(args.tag) > 200:
        parser.error("--tag must be a nonempty tag without control characters")
    if args.expected_commit and not re.fullmatch(r"[0-9a-fA-F]{40}", args.expected_commit):
        parser.error("--expected-commit must be a full 40-character SHA")
    if args.workflow and not re.fullmatch(r"[A-Za-z0-9_.-]+", args.workflow):
        parser.error("--workflow must be a workflow file name or numeric ID")
    if args.download and not args.asset:
        parser.error("--download requires --asset")
    if args.sha256 and (not args.download or not re.fullmatch(r"[0-9a-fA-F]{64}", args.sha256)):
        parser.error("--sha256 requires --download and a 64-character hex digest")
    if not 1 <= args.max_bytes <= 500_000_000:
        parser.error("--max-bytes must be between 1 and 500000000")
    try:
        result = check(args)
    except Exception as exc:
        print(json.dumps({"error": "unexpected checker error", "detail": type(exc).__name__}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
