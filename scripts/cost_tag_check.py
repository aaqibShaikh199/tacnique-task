"""
B2, part 2 — implement the cost-tagging check.

Read fixtures/plan.json for the shape of a `terraform show -json` plan: a `resource_changes`
list, where each entry has a `type`, an `address`, and `change.after.tags`.

Implement check_plan() so it:
  - Looks at every resource being created or updated (skip anything whose change.actions
    isn't "create" or "update" — a "no-op"/"read" change, or a "delete" with no `after`
    block at all).
  - Fails (returns a non-zero exit code) if the resource is missing the tag that identifies
    the real billing unit, per README.md's domain model — not whatever tag the resource
    happens to already carry.
  - Is idempotent: running this twice against the same plan file produces the same result,
    with no duplicate output and no flipped pass/fail. This is about a single run being
    stable and repeatable — it does not require remembering anything between runs.
  - Prints which specific resource address(es) are missing the tag.

Run manually: python scripts/cost_tag_check.py fixtures/plan.json
"""
import json
import sys

# LandlordAccount is the billing unit. tenant_id is what several resources are
# tagged with today; that tag does not decide who is billed.
BILLING_TAG = "landlord_account_id"


def check_plan(plan_path: str) -> int:
    """
    Returns an exit code: 0 if every resource being created or updated has
    `landlord_account_id`, non-zero otherwise.
    """
    with open(plan_path, encoding="utf-8") as handle:
        plan = json.load(handle)

    # Dedup key is the Terraform address. It is rebuilt from the file on every
    # call, so a second run cannot accumulate lines from the first.
    missing_addresses: set[str] = set()

    for resource in plan.get("resource_changes") or []:
        change = resource.get("change") or {}
        actions = change.get("actions") or []
        if "create" not in actions and "update" not in actions:
            continue

        after = change.get("after")
        tags = after.get("tags") if isinstance(after, dict) else None
        if not isinstance(tags, dict):
            tags = {}

        tag_value = tags.get(BILLING_TAG)
        if isinstance(tag_value, str) and tag_value.strip():
            continue

        address = resource.get("address")
        if isinstance(address, str) and address:
            missing_addresses.add(address)

    for address in sorted(missing_addresses):
        print(address)

    return 1 if missing_addresses else 0


if __name__ == "__main__":
    sys.exit(check_plan(sys.argv[1]))
