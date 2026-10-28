"""Office scripts, the authority hook, and the standalone export."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

OFFICE = Path(__file__).resolve().parents[1]
REPO = None
for candidate in [OFFICE, *OFFICE.parents]:
    if (candidate / "harness" / "export-chief-of-staff.sh").is_file():
        REPO = candidate
        break

sys.path.insert(0, str(OFFICE / "scripts"))
if REPO is not None:
    sys.path.insert(0, str(REPO / "harness" / "scripts"))

import budget_flags  # noqa: E402
import cycle_time  # noqa: E402
import dora  # noqa: E402
import pull_delivery  # noqa: E402
import run_due  # noqa: E402
import working_days  # noqa: E402
from office_env import parse_env_file  # noqa: E402


def load_guard():
    path = OFFICE / "scripts" / "guard_authority.py"
    if not path.is_file() and REPO is not None:
        path = REPO / "harness" / "scripts" / "guard_authority.py"
    spec = importlib.util.spec_from_file_location("guard_authority", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load_guard()
FIXTURES = Path(__file__).resolve().parent / "fixtures"


class WorkingDayTests(unittest.TestCase):
    def test_fifth_working_day_of_october_2026(self):
        self.assertEqual(working_days.working_day_number(date(2026, 10, 7), set()), 5)
        self.assertIsNone(working_days.working_day_number(date(2026, 10, 3), set()))

    def test_holiday_shifts_the_count(self):
        holidays = {date(2026, 10, 5)}
        self.assertEqual(working_days.working_day_number(date(2026, 10, 8), holidays), 5)

    def test_board_pack_is_ten_working_days_before(self):
        board = date(2026, 11, 13)
        due = working_days.subtract_working_days(board, 10, set())
        self.assertEqual(working_days.board_due(due, [board], 10, set()), board)
        self.assertIsNone(working_days.board_due(due + timedelta(days=1), [board], 10, set()))

    def test_quarterly_plan_is_one_week_before_the_quarter(self):
        self.assertTrue(working_days.quarterly_due(date(2026, 9, 24), 7, set()))
        self.assertFalse(working_days.quarterly_due(date(2026, 10, 1), 7, set()))

    def test_weekend_deadline_moves_to_the_previous_working_day(self):
        # 1 January 2027 is a Friday. Six calendar days before is Wednesday
        # 26 December 2026? Use a lead that lands on Sunday 27 December 2026:
        # next quarter from that Sunday is 1 January, and 1 Jan minus 5 days
        # is 27 Dec 2026, a Sunday, so the run is Friday 25 December.
        sunday = date(2026, 12, 27)
        self.assertEqual(sunday.strftime("%A"), "Sunday")
        nominal = date(2027, 1, 1) - timedelta(days=5)
        self.assertEqual(nominal, sunday)
        self.assertTrue(working_days.quarterly_due(date(2026, 12, 25), 5, set()))
        self.assertFalse(working_days.quarterly_due(sunday, 5, set()))


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.delivery = json.loads((FIXTURES / "delivery.json").read_text(encoding="utf-8"))

    def test_dora_uses_production_deployments_and_leaves_nothing_implied(self):
        result = dora.compute(self.delivery)
        self.assertFalse(result["using_proxy"])
        self.assertEqual(result["deployment_count"], 2)
        self.assertEqual(result["deployment_frequency_per_day"], round(2 / 7, 4))
        self.assertEqual(result["lead_time_hours_median"], 14)
        self.assertEqual(result["change_fail_rate"], 0.5)
        self.assertEqual(result["mttr_hours_median"], 4)

    def test_merged_pull_requests_are_a_labelled_proxy_and_not_a_failure_rate(self):
        document = dict(self.delivery)
        document["deployments"] = []
        document["incidents"] = []
        result = dora.compute(document)
        self.assertTrue(result["using_proxy"])
        self.assertIsNone(result["change_fail_rate"])
        self.assertIsNone(result["mttr_hours_median"])
        self.assertEqual(result["deployment_count"], 2)

    def test_cycle_time_excludes_a_missing_start(self):
        result = cycle_time.compute(self.delivery)
        self.assertEqual(result["cycle_time_hours_median"], 36)
        self.assertEqual(result["samples"], 2)
        self.assertEqual(result["excluded_missing_start"], ["ENG-3"])

    def test_budget_flags_caps_headcount_and_consultants(self):
        rows = budget_flags.read_csv(FIXTURES / "actuals.csv")
        config = {
            "SPEND_CAP_ITEM": "10000",
            "SPEND_CAP_ANNUAL": "40000",
            "SPEND_CAP_CONSULTANT": "25000",
            "SPEND_CAP_CONSULTANT_MONTHS": "3",
            "SPEND_CURRENCY": "GBP",
        }
        result = budget_flags.evaluate(rows, config, date(2026, 10, 7))
        by_item = {row["item"]: row for row in result["rows"]}
        self.assertEqual(by_item["Example tracker"]["decision"], "within_cap")
        self.assertEqual(by_item["Example platform"]["decision"], "within_cap")
        self.assertIn("consultant_over_cap", by_item["Example workshop"]["reasons"])
        self.assertIn("consultant_term_over_cap", by_item["Example workshop"]["reasons"])
        self.assertIn("people_decision", by_item["Open role"]["reasons"])
        self.assertEqual(result["annual_decision"], "needs_human")
        self.assertTrue(result["needs_human"])

    def test_equal_to_the_cap_is_within_it(self):
        rows = [{"category": "software", "item": "Renewal", "amount": "10000", "committed_on": "2026-10-01", "term_months": ""}]
        config = {
            "SPEND_CAP_ITEM": "10000",
            "SPEND_CAP_ANNUAL": "40000",
            "SPEND_CAP_CONSULTANT": "25000",
            "SPEND_CAP_CONSULTANT_MONTHS": "3",
        }
        result = budget_flags.evaluate(rows, config, date(2026, 10, 7))
        self.assertEqual(result["rows"][0]["decision"], "within_cap")
        self.assertFalse(result["needs_human"])

    def test_jira_start_comes_from_the_changelog_when_present(self):
        issue = {
            "key": "ENG-9",
            "fields": {
                "summary": "Example",
                "status": {"name": "Done"},
                "priority": {"name": "Medium"},
                "issuetype": {"name": "Task"},
                "created": "2026-10-01T00:00:00.000+0000",
                "resolutiondate": "2026-10-04T00:00:00.000+0000",
                "statuscategorychangedate": "2026-10-04T00:00:00.000+0000",
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2026-10-02T09:00:00.000+0000",
                        "items": [{"field": "status", "toString": "In Progress"}],
                    }
                ]
            },
        }
        normalised = pull_delivery.normalise_jira_issue(issue)
        self.assertEqual(normalised["started_at_source"], "changelog")
        self.assertTrue(normalised["started_at"].startswith("2026-10-02"))


class AuthorityTests(unittest.TestCase):
    def decide(self, tool, **payload):
        verdict, _reason = GUARD.decide({"tool_name": tool, "tool_input": payload}, OFFICE)
        return verdict

    def test_reads_and_office_writes_are_allowed(self):
        self.assertEqual(self.decide("Read", file_path="CLAUDE.md"), "approve")
        self.assertEqual(self.decide("Write", file_path="outputs/weekly/status.md"), "approve")
        self.assertEqual(self.decide("Edit", file_path="drafts/for-cto/spend.md"), "approve")
        self.assertEqual(self.decide("Bash", command="python3 scripts/dora.py"), "approve")
        self.assertEqual(self.decide("Bash", command="gh issue create --title 'Capacity note'"), "approve")
        self.assertEqual(self.decide("Bash", command="git status && git log -1"), "approve")
        self.assertEqual(self.decide("Bash", command="cat CLAUDE.md"), "approve")
        self.assertEqual(self.decide("Agent", subagent_type="weekly-delivery"), "approve")
        self.assertEqual(self.decide("mcp__linear__list_issues"), "approve")

    def test_code_changes_and_reprioritisation_are_denied(self):
        self.assertEqual(self.decide("Write", file_path="src/main.py"), "deny")
        self.assertEqual(self.decide("Bash", command="git status && git commit -m 'no'"), "deny")
        self.assertEqual(self.decide("Bash", command="gh pr merge 12"), "deny")
        self.assertEqual(self.decide("Bash", command="gh pr review 12 --approve"), "deny")
        self.assertEqual(self.decide("Bash", command='git commit -m "keep the && inside quotes"'), "deny")
        self.assertEqual(self.decide("Agent", subagent_type="development-team"), "deny")
        self.assertEqual(self.decide("mcp__linear__update_issue"), "deny")
        self.assertEqual(self.decide("mcp__jira__transition_issue"), "deny")
        self.assertEqual(self.decide("Bash", command="cat /etc/passwd"), "deny")
        self.assertEqual(self.decide("Bash", command="cat config/.env"), "deny")
        self.assertEqual(
            self.decide("Bash", command="python3 scripts/dora.py --output ../../outside.json"),
            "deny",
        )

    def test_env_file_cannot_run_a_command(self):
        with self.assertRaises(ValueError):
            parse_env_file("SPEND_CAP_ITEM=$(echo owned)\n")


class ScheduleTests(unittest.TestCase):
    def test_list_matches_the_responsibility_calendar(self):
        env = os.environ.copy()
        env["OFFICE_ROOT"] = str(OFFICE)
        env["OFFICE_TZ"] = "UTC"
        env["BOARD_DATES"] = "2026-11-13"
        friday = subprocess.run(
            [sys.executable, "scripts/run_due.py", "--list", "--at", "2026-10-02T17:00:00"],
            cwd=OFFICE,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("weekly-delivery: due", friday.stdout)
        self.assertIn("budget: skip", friday.stdout)
        wednesday = subprocess.run(
            [sys.executable, "scripts/run_due.py", "--list", "--at", "2026-10-07T08:30:00"],
            cwd=OFFICE,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("budget: due", wednesday.stdout)
        self.assertIn("weekly-delivery: skip", wednesday.stdout)
        quarter = subprocess.run(
            [sys.executable, "scripts/run_due.py", "--list", "--at", "2026-09-24T08:35:00"],
            cwd=OFFICE,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("quarterly-plan: due", quarter.stdout)
        board_day = working_days.subtract_working_days(date(2026, 11, 13), 10, set())
        board = subprocess.run(
            [sys.executable, "scripts/run_due.py", "--list", "--at", f"{board_day.isoformat()}T08:40:00"],
            cwd=OFFICE,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("board-pack: due", board.stdout)

    def test_dry_run_does_not_invoke_claude(self):
        env = os.environ.copy()
        env["OFFICE_ROOT"] = str(OFFICE)
        env["OFFICE_TZ"] = "UTC"
        env["PATH"] = "/usr/bin:/bin"
        completed = subprocess.run(
            [sys.executable, "scripts/run_due.py", "--job", "weekly-delivery", "--at", "2026-10-02T17:00:00", "--dry-run"],
            cwd=OFFICE,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("claude-headless.sh", completed.stdout)
        self.assertIn("--dry-run", completed.stdout)
        self.assertNotIn("total_cost_usd", completed.stdout)


class ExportTests(unittest.TestCase):
    def test_standalone_export_has_no_delivery_team(self):
        if REPO is None:
            self.skipTest("export script is in the toolkit, not in a work checkout")
        script = REPO / "harness" / "export-chief-of-staff.sh"
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cto-office"
            completed = subprocess.run(["bash", str(script), str(dest)], check=False, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((dest / "CLAUDE.md").is_file())
            self.assertTrue((dest / ".mcp.json").is_file())
            self.assertTrue((dest / ".claude" / "agents" / "weekly-delivery.md").is_file())
            self.assertTrue((dest / ".claude" / "skills" / "human-escalation" / "SKILL.md").is_file())
            self.assertTrue((dest / "scripts" / "guard_authority.py").is_file())
            self.assertTrue((dest / "scripts" / "pull_delivery.py").is_file())
            delivery_tree = "starter-" + "delivery-team"
            self.assertFalse((dest / delivery_tree).exists())
            names = [path.name for path in dest.rglob("*")]
            self.assertNotIn("pipeline" + "ctl", names)
            self.assertNotIn("jira" + "ctl", names)
            blob = "\n".join(
                path.read_text(encoding="utf-8", errors="ignore")
                for path in dest.rglob("*")
                if path.is_file() and path.suffix in {".md", ".json", ".py", ".sh", ".example", ".txt"}
            )
            banned_names = (
                delivery_tree,
                "pipeline" + "ctl",
                "jira" + "ctl",
                "/" + "Users/",
                "atlassian" + ".net",
                "gh" + "p_",
                "sk-" + "ant-",
            )
            for banned in banned_names:
                self.assertNotIn(banned, blob)
            mcp = json.loads((dest / ".mcp.json").read_text(encoding="utf-8"))
            self.assertIn("${GITHUB_TOKEN}", json.dumps(mcp))
            hook = (dest / ".claude" / "agents" / "budget-tracker.md").read_text(encoding="utf-8")
            self.assertIn("scripts/guard_authority.py", hook)
            self.assertNotIn("../../harness", hook)
            dry = subprocess.run(
                ["bash", "scripts/claude-headless.sh", "--dry-run", "--agent", "weekly-delivery", "--prompt-file", "schedules/prompts/weekly-delivery.md"],
                cwd=dest,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn("claude", dry.stdout)
            self.assertIn("--permission-mode", dry.stdout)
            printed = subprocess.run(
                ["bash", "scripts/install-schedule.sh", "--print"],
                cwd=dest,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(printed.returncode, 0, printed.stderr)
            self.assertIn("weekly-delivery", printed.stdout)
            self.assertIn("run-due.sh", printed.stdout)
            rerun = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                cwd=dest,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rerun.returncode, 0, rerun.stderr + rerun.stdout)


class SettingsParityTests(unittest.TestCase):
    def test_template_and_harness_permissions_match(self):
        if REPO is None:
            self.skipTest("harness settings live in the toolkit")
        harness = json.loads((REPO / "harness" / "claude" / "settings.json").read_text(encoding="utf-8"))
        team = json.loads((OFFICE / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(harness["permissions"]["allow"], team["permissions"]["allow"])
        self.assertEqual(harness["permissions"]["deny"], team["permissions"]["deny"])


if __name__ == "__main__":
    unittest.main()
