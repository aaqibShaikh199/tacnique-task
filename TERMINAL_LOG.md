# Terminal log

Setup, both B2 test modules, and two runs of the cost-tag check against the unchanged
`fixtures/plan.json`. Commands were run from the repository root. `.venv/` is local and is
not part of the submission.

The B0 plan was run from `terraform/` with Terraform 1.7.5 after `terraform init` installed
`hashicorp/aws` v5.100.0. The default list was temporarily `["la-001", "la-003", "la-004"]`,
then `variables.tf` was restored. `terraform.tfstate` checksum before and after that plan:

```text
7ad36b88f2ca839798b0b8d04fe17d69c921a076  terraform.tfstate
```

The plan text itself is quoted in `B0.md`. It was `terraform plan -refresh=false -input=false`.

## Setup

```text
$ python3 --version
Python 3.14.6

$ terraform version
Terraform v1.7.5
on darwin_arm64

$ terraform init -input=false
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!

$ python3 -m venv .venv
$ PIP_USER=0 .venv/bin/pip install -r requirements.txt
Requirement already satisfied: pytest>=8.0 in ./.venv/lib/python3.14/site-packages (from -r requirements.txt (line 1)) (9.2.0)
Requirement already satisfied: iniconfig>=2 in ./.venv/lib/python3.14/site-packages (from pytest>=8.0->-r requirements.txt (line 1)) (2.3.1)
Requirement already satisfied: packaging>=24 in ./.venv/lib/python3.14/site-packages (from pytest>=8.0->-r requirements.txt (line 1)) (26.3)
Requirement already satisfied: pluggy<2,>=1.6 in ./.venv/lib/python3.14/site-packages (from pytest>=8.0->-r requirements.txt (line 1)) (1.7.0)
Requirement already satisfied: pygments>=2.15 in ./.venv/lib/python3.14/site-packages (from pytest>=8.0->-r requirements.txt (line 1)) (2.21.0)
```

## B2 test run — access check

```text
$ .venv/bin/python -m pytest -v tests/test_access_control.py
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0 -- /Users/apple/Desktop/tacnique-task/starter/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/apple/Desktop/tacnique-task/starter
collecting ... collected 3 items

tests/test_access_control.py::test_cross_account_screening_report_is_denied PASSED [ 33%]
tests/test_access_control.py::test_same_account_screening_report_is_allowed PASSED [ 66%]
tests/test_access_control.py::test_missing_tenant_or_property_fails_closed PASSED [100%]

============================== 3 passed in 0.01s ===============================
```

Exit code: 0

## B2 test run — cost-tag check

```text
$ .venv/bin/python -m pytest -v tests/test_cost_tag_check.py
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0 -- /Users/apple/Desktop/tacnique-task/starter/.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/apple/Desktop/tacnique-task/starter
collecting ... collected 7 items

tests/test_cost_tag_check.py::test_shared_plan_flags_only_resources_missing_billing_tag PASSED [ 14%]
tests/test_cost_tag_check.py::test_second_run_against_unchanged_plan_matches_the_first PASSED [ 28%]
tests/test_cost_tag_check.py::test_tag_check_is_not_hardcoded_to_the_fixture_resources PASSED [ 42%]
tests/test_cost_tag_check.py::test_duplicate_address_in_one_plan_is_reported_once PASSED [ 57%]
tests/test_cost_tag_check.py::test_plan_with_billing_tag_on_every_change_passes PASSED [ 71%]
tests/test_cost_tag_check.py::test_replacement_is_checked_because_create_is_in_the_actions PASSED [ 85%]
tests/test_cost_tag_check.py::test_delete_without_after_and_noop_are_ignored PASSED [100%]

============================== 7 passed in 0.02s ===============================
```

Exit code: 0

## Cost-tag check, twice, same plan file

Both runs exit 1. That is the same result: the plan still has two resources missing
`landlord_account_id`. The lines are identical and neither address is repeated. Idempotency
here is "same output, same exit code," not "the second run passes."

```text
$ .venv/bin/python scripts/cost_tag_check.py fixtures/plan.json
aws_lambda_function.mls_feed_sync
aws_s3_bucket.listing_media
$ echo $?
1

$ .venv/bin/python scripts/cost_tag_check.py fixtures/plan.json
aws_lambda_function.mls_feed_sync
aws_s3_bucket.listing_media
$ echo $?
1
```
