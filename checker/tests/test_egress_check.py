"""Fixtures are single steps copied from published DeepSWE v1.1 trajectories."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import egress_check as ec  # noqa: E402

FIXTURES = json.loads((Path(__file__).parent / "fixtures.json").read_text())


def labels(name: str) -> list[str]:
    fixture = FIXTURES[name]
    return [a.label for a in ec.check_trajectory(fixture["trial"], fixture)]


class RealSteps(unittest.TestCase):
    def test_curl_of_upstream_source_is_reached(self):
        self.assertEqual(labels("reached_curl"), ["reached"])

    def test_pip_download_from_pypi_is_reached(self):
        self.assertEqual(labels("reached_pip"), ["reached"])

    def test_github_api_json_is_reached(self):
        self.assertEqual(labels("reached_api"), ["reached"])

    def test_squid_refusal_is_blocked(self):
        self.assertEqual(labels("blocked_curl"), ["blocked"])

    def test_pip_through_refusing_proxy_is_blocked(self):
        self.assertEqual(labels("blocked_pip"), ["blocked"])

    def test_squid_error_page_saved_with_exit_0_is_not_reached(self):
        self.assertEqual(labels("squid_page_200"), ["unclear"])

    def test_reading_source_that_mentions_proxyerror_is_not_an_attempt(self):
        self.assertEqual(labels("fp_source_text"), [])

    def test_editable_install_of_the_repo_is_not_an_attempt(self):
        self.assertEqual(labels("fp_editable"), [])

    def test_urlopen_that_gets_a_remote_404_is_reached(self):
        self.assertIn("reached", labels("reached_urlopen_404"))

    def test_test_file_written_with_a_heredoc_is_not_an_attempt(self):
        self.assertEqual(labels("fp_heredoc_file"), [])

    def test_local_traceback_is_not_reached(self):
        self.assertNotIn("reached", labels("fp_traceback"))

    def test_installing_a_local_wheel_is_not_an_attempt(self):
        self.assertEqual(labels("fp_local_wheel"), [])


class Parsing(unittest.TestCase):
    def test_localhost_curl_is_not_an_attempt(self):
        self.assertIsNone(ec.NETWORK_ATTEMPT.search("curl -s http://localhost:8000/health"))

    def test_json_wrapped_output_is_unwrapped(self):
        self.assertEqual(ec._output_text('{"returncode": 0, "output": "hi"}'), "hi")
        self.assertEqual(ec._output_text('{"returncode": 0, "output_head": "head"}'), "head")
        self.assertEqual(ec._output_text("plain"), "plain")

    def test_source_lines_count_only_when_the_command_fetched_a_url(self):
        out = "import os\nfrom x import y\n"
        self.assertEqual(ec.label_output(out, "go get example.com/x")[0], "unclear")
        self.assertEqual(ec.label_output(out, "curl -s https://example.com/a.py")[0], "reached")

    def test_blocked_wins_over_reached_markers(self):
        self.assertEqual(ec.label_output("import os\ncurl: (56) CONNECT tunnel failed, response 403")[0], "blocked")

    def test_summary_counts_trials_once_per_label(self):
        a = ec.Attempt("t1", 1, "curl https://x", "", "blocked", "")
        b = ec.Attempt("t1", 2, "curl https://y", "", "blocked", "")
        c = ec.Attempt("t2", 1, "curl https://z", "", "reached", "")
        s = ec.summarize({"t1": [a, b], "t2": [c], "t3": []})
        self.assertEqual(s["trials_checked"], 3)
        self.assertEqual(s["trials_with_attempts"], 2)
        self.assertEqual(s["attempts"], {"blocked": 2, "reached": 1})
        self.assertEqual(s["trials_by_label"], {"blocked": 1, "reached": 1})

    def test_published_trials_sample_is_per_config_and_seeded(self):
        import tempfile
        rows = [{"trial_name": f"{c}{i}", "config": c, "has_trajectory": True} for c in "ab" for i in range(5)]
        rows.append({"trial_name": "nolog", "config": "a", "has_trajectory": False})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trials.json"
            path.write_text(json.dumps({"rows": rows}))
            first = ec.published_trials(path, ["all"], 2)
            self.assertEqual(len(first), 4)
            self.assertEqual(first, ec.published_trials(path, ["all"], 2))
            self.assertEqual(len(ec.published_trials(path, ["a"])), 5)

    def test_job_dir_layout(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            trial = Path(tmp) / "task__abc" / "agent"
            trial.mkdir(parents=True)
            (trial / "trajectory.json").write_text(json.dumps(FIXTURES["reached_curl"]))
            self.assertEqual(ec.main(["--job-dir", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
