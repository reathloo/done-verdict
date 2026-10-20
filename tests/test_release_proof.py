import importlib.util
import hashlib
import io
import json
import pathlib
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch


PATH = pathlib.Path(__file__).resolve().parents[1] / "skills/done-verdict/scripts/release_proof.py"
SPEC = importlib.util.spec_from_file_location("release_proof", PATH)
proof = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proof)
SHA = "a" * 40


class ReleaseProofTests(unittest.TestCase):
    def run_check(self, responses, *extra):
        def fake_fetch(url, limit=2_000_000):
            for suffix, value in responses.items():
                if url.endswith(suffix):
                    if isinstance(value, Exception):
                        raise value
                    data = value if isinstance(value, bytes) else json.dumps(value).encode()
                    if len(data) > limit:
                        raise proof.FetchError("response exceeds size limit")
                    return data
            raise AssertionError("Unexpected URL: " + url)

        with patch.object(proof, "fetch", side_effect=fake_fetch):
            argv = ["--repo", "owner/project", "--tag", "v1"] + list(extra)
            with patch("builtins.print") as printed:
                exit_code = proof.main(argv)
            self.assertEqual(exit_code, 0)
            return json.loads(printed.call_args.args[0])

    def base(self, **release_overrides):
        release = {"draft": False, "published_at": "2026-01-01T00:00:00Z", "html_url": "https://github.com/owner/project/releases/tag/v1", "assets": []}
        release.update(release_overrides)
        return {"/git/ref/tags/v1": {"ref": "refs/tags/v1", "object": {"type": "commit", "sha": SHA}}, "/releases/tags/v1": release}

    def statuses(self, result):
        return {item["claim"]: item["status"] for item in result["claims"]}

    def test_exact_commit_and_public_release(self):
        result = self.run_check(self.base(), "--expected-commit", SHA)
        self.assertEqual(self.statuses(result), {"tag_commit": "supported", "public_release": "supported"})
        self.assertIn("No artifact installation or execution", result["limits"])
        self.assertEqual(result["requested"]["expected_commit"], SHA)

    def test_annotated_tag_resolves_to_commit(self):
        responses = self.base()
        tag_object_sha = "c" * 40
        responses["/git/ref/tags/v1"] = {"ref": "refs/tags/v1", "object": {"type": "tag", "sha": tag_object_sha}}
        responses["/git/tags/" + tag_object_sha] = {"object": {"type": "commit", "sha": SHA}}
        result = self.run_check(responses, "--expected-commit", SHA)
        self.assertEqual(self.statuses(result)["tag_commit"], "supported")

    def test_missing_annotated_object_is_unknown_not_missing_tag(self):
        responses = self.base()
        tag_object_sha = "c" * 40
        responses["/git/ref/tags/v1"] = {"ref": "refs/tags/v1", "object": {"type": "tag", "sha": tag_object_sha}}
        responses["/git/tags/" + tag_object_sha] = proof.FetchError("HTTP 404", 404)
        result = self.run_check(responses)
        self.assertEqual(self.statuses(result)["tag_commit"], "unknown")

    def test_same_named_branch_is_not_a_tag(self):
        responses = self.base()
        responses["/git/ref/tags/v1"] = proof.FetchError("HTTP 404", 404)
        result = self.run_check(responses)
        self.assertEqual(self.statuses(result)["tag_commit"], "contradicted")

    def test_invalid_tag_target_is_unknown(self):
        responses = self.base()
        responses["/git/ref/tags/v1"] = {"ref": "refs/tags/v1", "object": {"type": "tree", "sha": SHA}}
        result = self.run_check(responses)
        self.assertEqual(self.statuses(result)["tag_commit"], "unknown")

    def test_malformed_tag_and_assets_are_unknown(self):
        responses = self.base(assets=None)
        responses["/git/ref/tags/v1"] = []
        result = self.run_check(responses, "--asset", "app.zip")
        self.assertEqual(self.statuses(result)["tag_commit"], "unknown")
        self.assertEqual(self.statuses(result)["asset_listed"], "unknown")

    def test_wrong_commit_and_draft(self):
        result = self.run_check(self.base(draft=True), "--expected-commit", "b" * 40)
        self.assertEqual(self.statuses(result), {"tag_commit": "contradicted", "public_release": "contradicted"})

    def test_missing_tag_and_release(self):
        missing = proof.FetchError("HTTP 404", 404)
        result = self.run_check({"/git/ref/tags/v1": missing, "/releases/tags/v1": missing}, "--workflow", "ci.yml", "--asset", "app.zip")
        self.assertEqual(self.statuses(result), {"tag_commit": "contradicted", "public_release": "contradicted", "workflow": "unknown", "asset_listed": "unknown"})

    def test_rate_limit_is_unknown(self):
        rate_limit = proof.FetchError("HTTP 403", 403)
        result = self.run_check({"/git/ref/tags/v1": rate_limit, "/releases/tags/v1": rate_limit})
        self.assertEqual(self.statuses(result), {"tag_commit": "unknown", "public_release": "unknown"})

    def test_missing_asset(self):
        result = self.run_check(self.base(), "--asset", "app.zip", "--download")
        self.assertEqual(self.statuses(result)["asset_listed"], "contradicted")
        self.assertNotIn("anonymous_download", self.statuses(result))

    def test_anonymous_download_and_checksum(self):
        payload = b"real artifact bytes"
        asset_url = "https://github.com/owner/project/releases/download/v1/app.zip"
        asset = {"name": "app.zip", "state": "uploaded", "size": len(payload), "browser_download_url": asset_url, "digest": "sha256:" + hashlib.sha256(payload).hexdigest()}
        responses = self.base(assets=[asset])
        responses["/download/v1/app.zip"] = payload
        result = self.run_check(responses, "--asset", "app.zip", "--download")
        self.assertEqual(self.statuses(result)["anonymous_download"], "supported")
        self.assertEqual(self.statuses(result)["checksum"], "supported")

    def test_both_digest_sources_are_checked(self):
        payload = b"data"
        correct = hashlib.sha256(payload).hexdigest()
        asset = {"name": "app.zip", "state": "uploaded", "size": len(payload), "browser_download_url": "https://github.com/owner/project/releases/download/v1/app.zip", "digest": "sha256:" + "0" * 64}
        responses = self.base(assets=[asset])
        responses["/download/v1/app.zip"] = payload
        result = self.run_check(responses, "--asset", "app.zip", "--download", "--sha256", correct)
        self.assertEqual(self.statuses(result)["checksum"], "contradicted")
        self.assertIn("supplied SHA-256", next(item["detail"] for item in result["claims"] if item["claim"] == "checksum"))

    def test_prerelease_is_visible_in_result(self):
        result = self.run_check(self.base(prerelease=True))
        self.assertIn("Published prerelease", next(item["detail"] for item in result["claims"] if item["claim"] == "public_release"))

    def test_bad_checksum_and_size_limit(self):
        asset = {"name": "app.zip", "state": "uploaded", "size": 4, "browser_download_url": "https://github.com/owner/project/releases/download/v1/app.zip", "digest": "sha256:" + "0" * 64}
        responses = self.base(assets=[asset])
        responses["/download/v1/app.zip"] = b"data"
        result = self.run_check(responses, "--asset", "app.zip", "--download")
        self.assertEqual(self.statuses(result)["checksum"], "contradicted")
        result = self.run_check(responses, "--asset", "app.zip", "--download", "--max-bytes", "3")
        self.assertEqual(self.statuses(result)["anonymous_download"], "unknown")

    def test_download_wrong_size_is_not_accepted(self):
        asset = {"name": "app.zip", "state": "uploaded", "size": 999, "browser_download_url": "https://github.com/owner/project/releases/download/v1/app.zip"}
        responses = self.base(assets=[asset])
        responses["/download/v1/app.zip"] = b"possibly an HTML error page"
        result = self.run_check(responses, "--asset", "app.zip", "--download")
        self.assertEqual(self.statuses(result)["anonymous_download"], "contradicted")

    def test_download_missing_size_is_unknown(self):
        asset = {"name": "app.zip", "state": "uploaded", "size": None, "browser_download_url": "https://github.com/owner/project/releases/download/v1/app.zip"}
        responses = self.base(assets=[asset])
        responses["/download/v1/app.zip"] = b"data"
        result = self.run_check(responses, "--asset", "app.zip", "--download")
        self.assertEqual(self.statuses(result)["anonymous_download"], "unknown")

    def test_wrong_ref_workflow_ignored(self):
        responses = self.base()
        responses["head_sha=" + SHA + "&per_page=100"] = {"workflow_runs": [{"head_sha": "b" * 40, "status": "completed", "conclusion": "success"}]}
        result = self.run_check(responses, "--workflow", "ci.yml")
        self.assertEqual(self.statuses(result)["workflow"], "unknown")

    def test_workflow_success_failure_and_pending(self):
        for status, conclusion, expected in [("completed", "success", "supported"), ("completed", "failure", "contradicted"), ("in_progress", None, "unknown")]:
            with self.subTest(status=status, conclusion=conclusion):
                responses = self.base()
                responses["head_sha=" + SHA + "&per_page=100"] = {"workflow_runs": [{"head_sha": SHA, "status": status, "conclusion": conclusion, "created_at": "2026-01-01T00:00:00Z"}]}
                result = self.run_check(responses, "--workflow", "ci.yml")
                self.assertEqual(self.statuses(result)["workflow"], expected)

    def test_invalid_inputs_fail_before_network(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            proof.main(["--repo", "owner/project", "--tag", "v1", "--download"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
