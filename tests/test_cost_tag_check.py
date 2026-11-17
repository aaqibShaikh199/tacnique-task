"""
Write tests here proving:
  1. Happy path: running the check against fixtures/plan.json correctly flags the resources
     missing `landlord_account_id` (listing_media, mls_feed_sync) and passes the ones that
     have it (landlord_media[0], screening_report_export). The fixture also has a "no-op"
     entry and a "delete" entry with no `after` block at all — neither should appear in the
     output or crash the check.
  2. Idempotency: running the check twice against the same plan file produces the same
     result both times, with no duplicated output.

check_plan() takes a file path, not a dict — for a case that needs its own plan contents
instead of the shared fixture, write one with pytest's `tmp_path` rather than editing
fixtures/plan.json. You don't need to shell out to the real script for every case.
"""
import json
from pathlib import Path

from scripts.cost_tag_check import check_plan

PLAN_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "plan.json"

MISSING = [
    "aws_lambda_function.mls_feed_sync",
    "aws_s3_bucket.listing_media",
]


def _write_plan(path: Path, resource_changes: list) -> Path:
    path.write_text(
        json.dumps({"format_version": "1.2", "resource_changes": resource_changes}),
        encoding="utf-8",
    )
    return path


def _resource(address: str, actions: list, tags=None, after=...):
    change = {"actions": actions}
    if after is ...:
        change["after"] = {"tags": {} if tags is None else tags}
    else:
        change["after"] = after
    return {"address": address, "change": change}


def test_shared_plan_flags_only_resources_missing_billing_tag(capsys):
    exit_code = check_plan(str(PLAN_PATH))
    output = capsys.readouterr().out.splitlines()

    assert exit_code == 1
    assert output == MISSING
    assert "aws_s3_bucket.landlord_media[0]" not in output
    assert "aws_lambda_function.screening_report_export" not in output
    assert "aws_s3_bucket.archive_media" not in output
    assert "aws_s3_bucket.decommissioned_media" not in output


def test_second_run_against_unchanged_plan_matches_the_first(capsys):
    first_code = check_plan(str(PLAN_PATH))
    first_output = capsys.readouterr().out
    second_code = check_plan(str(PLAN_PATH))
    second_output = capsys.readouterr().out

    assert first_code == second_code == 1
    assert first_output == second_output
    assert first_output.splitlines() == MISSING
    assert first_output.count("aws_s3_bucket.listing_media") == 1
    assert first_output.count("aws_lambda_function.mls_feed_sync") == 1


def test_tag_check_is_not_hardcoded_to_the_fixture_resources(tmp_path, capsys):
    plan_path = _write_plan(
        tmp_path / "plan.json",
        [
            _resource(
                "aws_sqs_queue.billing_events",
                ["create"],
                tags={"tenant_id": "ten-001"},
            ),
            _resource(
                "aws_dynamodb_table.ledger",
                ["update"],
                tags={"landlord_account_id": "la-009"},
            ),
        ],
    )

    exit_code = check_plan(str(plan_path))
    output = capsys.readouterr().out.splitlines()

    assert exit_code == 1
    assert output == ["aws_sqs_queue.billing_events"]


def test_duplicate_address_in_one_plan_is_reported_once(tmp_path, capsys):
    plan_path = _write_plan(
        tmp_path / "plan.json",
        [
            _resource("aws_s3_bucket.same", ["create"], tags={"tenant_id": "ten-001"}),
            _resource("aws_s3_bucket.same", ["update"], tags={}),
        ],
    )

    exit_code = check_plan(str(plan_path))
    output = capsys.readouterr().out

    assert exit_code == 1
    assert output == "aws_s3_bucket.same\n"


def test_plan_with_billing_tag_on_every_change_passes(tmp_path, capsys):
    plan_path = _write_plan(
        tmp_path / "plan.json",
        [
            _resource(
                "aws_s3_bucket.kept",
                ["create"],
                tags={"landlord_account_id": "la-001"},
            )
        ],
    )

    exit_code = check_plan(str(plan_path))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output == ""


def test_replacement_is_checked_because_create_is_in_the_actions(tmp_path, capsys):
    plan_path = _write_plan(
        tmp_path / "plan.json",
        [
            _resource(
                "aws_s3_bucket.replaced",
                ["delete", "create"],
                tags={"tenant_id": "ten-001"},
            )
        ],
    )

    exit_code = check_plan(str(plan_path))
    output = capsys.readouterr().out

    assert exit_code == 1
    assert output == "aws_s3_bucket.replaced\n"


def test_delete_without_after_and_noop_are_ignored(tmp_path, capsys):
    plan_path = _write_plan(
        tmp_path / "plan.json",
        [
            _resource("aws_s3_bucket.gone", ["delete"], after=None),
            _resource("aws_s3_bucket.unchanged", ["no-op"], tags={}),
            _resource("aws_s3_bucket.read_only", ["read"], tags={}),
        ],
    )

    exit_code = check_plan(str(plan_path))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output == ""
