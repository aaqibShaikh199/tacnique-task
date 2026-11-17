# Design Notes

## B2 — idempotency key

The key is the Terraform address, `resource_changes[].address`
(`aws_s3_bucket.listing_media`, `aws_lambda_function.mls_feed_sync`, and so on).

Inside one call, addresses that are missing `landlord_account_id` go into a set. Two entries
with the same address are the same resource, so they produce one output line. The set is
sorted before it is printed. Address is the right key because it already includes the module
path and the `count` or `for_each` index. Deduping on `type` plus `name` would collapse
`landlord_media[0]` and `landlord_media[1]` into one resource, which is the identity mistake
from B0.

That set lives on the stack for the call. The script does not append to a file, a module
global, or anywhere else that a second process could see. Each run opens the plan, builds the
set, prints the sorted addresses, and returns 0 or 1. The same file therefore produces the
same lines and the same exit code, with each missing address printed once. That is the
idempotency property: repeating the call does not change the result and does not require a
record of the previous call. Both runs exit 1 on `fixtures/plan.json` because the plan is
unchanged and still missing tags. A second run that suddenly exited 0 would be a different
result, not an idempotent one.

Output is only those addresses, one per line. No banner, so the two runs are byte-for-byte
the same.

## Any other decision with a non-obvious alternative

**Which actions count as "being created or updated."** A resource is in scope when `create`
or `update` is one of `change.actions`. A replacement is `["delete", "create"]`, and the
object that will exist afterward is the one that gets billed, so it is checked. The
alternative was to accept only a list that is exactly `["create"]` or exactly `["update"]`.
That skips replacements and lets a replaced bucket through with no `landlord_account_id`.
`no-op`, `read`, and a bare `delete` (including a delete whose `after` is null) are not
checked. The null `after` is why the delete entry cannot be inspected for tags; the action
is what skips it, before `after` is read.

**What "missing the tag" means.** The tag that fails the check is `landlord_account_id`,
because `LandlordAccount` is the billing unit in the domain model. A present `tenant_id` does
not satisfy it. `listing_media` in the fixture is tagged only with `tenant_id`, and that is
the case the check is supposed to fail. An empty or blank value counts as missing. The
alternative was to require whichever tag the resource already carried, which would pass
`listing_media` and fail to bill by landlord account.

**Where the access decision is made.** `can_access_screening_report` walks
report → tenant → property and allows the view only when
`PropertyManager.landlord_account_id` equals `Property.landlord_account_id`. A manager is
scoped to one landlord account, and every tenant under that account is in scope. Comparing
the manager to `tenant_id` or `property_id` would deny a manager their own other tenants, and
it would follow the ids that happen to be on the records rather than the account boundary.
If the tenant or the property is not in the lists passed in, the function returns false.
There is no separate allow on a missing link.

The check is generic over `resource_changes`. It does not name `listing_media` or
`mls_feed_sync`. The shared fixture covers those two failures, and a plan built under
`tmp_path` covers an unrelated resource type so the fixture addresses are not special.
